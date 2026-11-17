package main

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// buildQuery assembles a minimal DNS query with the given questions.
func buildQuery(id uint16, qs ...question) []byte {
	var b bytes.Buffer
	b.Write([]byte{byte(id >> 8), byte(id), 0x01, 0x00, 0x00, byte(len(qs)), 0, 0, 0, 0, 0, 0})
	for _, q := range qs {
		for _, label := range strings.Split(q.Name, ".") {
			b.WriteByte(byte(len(label)))
			b.WriteString(label)
		}
		b.WriteByte(0)
		b.Write([]byte{byte(q.Type >> 8), byte(q.Type), byte(q.Class >> 8), byte(q.Class)})
	}
	return b.Bytes()
}

// calls ServeHTTP directly to ensure we're testing the server logic, not the network
func post(
	t *testing.T,
	h http.Handler,
	body string,
	hdr map[string]string,
) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(http.MethodPost, "/dns/queries", strings.NewReader(body))
	for k, v := range hdr {
		req.Header.Set(k, v)
	}
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	return rec
}

func testHandler() (http.Handler, *bytes.Buffer) {
	var logs bytes.Buffer
	return newMux(slog.New(slog.NewJSONHandler(&logs, nil))), &logs
}

func TestQuery(t *testing.T) {
	h, logs := testHandler()
	msg := buildQuery(0xabcd,
		question{Name: "example.com", Type: 1, Class: 1},
		question{Name: "mail.example.org", Type: 15, Class: 1},
		question{Name: "v6.example.net", Type: 28, Class: 1},
	)
	body := base64.StdEncoding.EncodeToString(msg)

	rec := post(t, h, body, nil)
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, body = %s", rec.Code, rec.Body)
	}
	var got queryResponse
	if err := json.Unmarshal(rec.Body.Bytes(), &got); err != nil {
		t.Fatal(err)
	}
	want := []questionJSON{
		{"example.com", "A"},
		{"mail.example.org", "MX"},
		{"v6.example.net", "TYPE28"},
	}
	if len(got.Questions) != len(want) {
		t.Fatalf("questions = %+v", got.Questions)
	}
	for i := range want {
		if got.Questions[i] != want[i] {
			t.Errorf("question %d = %+v, want %+v", i, got.Questions[i], want[i])
		}
	}
	if rec.Header().Get("ETag") != `"`+got.ID+`"` {
		t.Errorf("ETag = %q, id = %q", rec.Header().Get("ETag"), got.ID)
	}
	if !strings.Contains(rec.Header().Get("Cache-Control"), "max-age=") {
		t.Errorf("Cache-Control = %q", rec.Header().Get("Cache-Control"))
	}
	if !strings.Contains(logs.String(), `"msg":"access"`) ||
		!strings.Contains(logs.String(), got.ID) {
		t.Errorf("expected access and response logs, got %s", logs)
	}
}

func TestSameBodySameID(t *testing.T) {
	h, _ := testHandler()
	a := base64.StdEncoding.EncodeToString(buildQuery(1, question{"a.test", 1, 1}))
	b := base64.StdEncoding.EncodeToString(buildQuery(2, question{"a.test", 1, 1}))

	id := func(body string) string {
		var r queryResponse
		_ = json.Unmarshal(post(t, h, body, nil).Body.Bytes(), &r)
		return r.ID
	}
	if id(a) != id(a) {
		t.Error("same body produced different IDs")
	}
	if id(a) == id(b) {
		t.Error("different bodies produced the same ID")
	}
}

func TestIfNoneMatch(t *testing.T) {
	h, _ := testHandler()
	body := base64.StdEncoding.EncodeToString(buildQuery(1, question{"a.test", 1, 1}))
	etag := post(t, h, body, nil).Header().Get("ETag")

	rec := post(t, h, body, map[string]string{"If-None-Match": etag})
	if rec.Code != http.StatusNotModified {
		t.Fatalf("status = %d", rec.Code)
	}
	if rec.Body.Len() != 0 {
		t.Errorf("304 had body %q", rec.Body)
	}
}

func TestURLSafeUnpadded(t *testing.T) {
	h, _ := testHandler()
	body := base64.RawURLEncoding.EncodeToString(buildQuery(0xfbff, question{"x.test", 255, 1}))
	rec := post(t, h, body+"\n", nil)
	if rec.Code != http.StatusOK || !strings.Contains(rec.Body.String(), `"type":"*"`) {
		t.Fatalf("status = %d, body = %s", rec.Code, rec.Body)
	}
}

func TestBadRequests(t *testing.T) {
	h, _ := testHandler()
	resp := buildQuery(1, question{"a.test", 1, 1})
	resp[2] |= 0x80

	truncated := buildQuery(1, question{"a.test", 1, 1})
	truncated = truncated[:len(truncated)-2]

	loop := buildQuery(1)
	loop[5] = 1
	loop = append(loop, 0xC0, 12, 0, 1, 0, 1) // pointer to itself

	cases := map[string]string{
		"not base64": "!!!",
		"too short":  base64.StdEncoding.EncodeToString([]byte{1, 2, 3}),
		"response":   base64.StdEncoding.EncodeToString(resp),
		"truncated":  base64.StdEncoding.EncodeToString(truncated),
		"ptr loop":   base64.StdEncoding.EncodeToString(loop),
	}
	for name, body := range cases {
		t.Run(name, func(t *testing.T) {
			rec := post(t, h, body, nil)
			if rec.Code != http.StatusBadRequest {
				t.Fatalf("status = %d, body = %s", rec.Code, rec.Body)
			}
		})
	}
}

func TestMethodNotAllowed(t *testing.T) {
	h, _ := testHandler()
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/dns/queries", nil))
	if rec.Code != http.StatusMethodNotAllowed {
		t.Fatalf("status = %d", rec.Code)
	}
}

func TestBodyTooLarge(t *testing.T) {
	h, _ := testHandler()
	rec := post(t, h, strings.Repeat("A", maxBodyBytes+4), nil)
	if rec.Code != http.StatusRequestEntityTooLarge {
		t.Fatalf("status = %d", rec.Code)
	}
}

func TestCompressedName(t *testing.T) {
	// Second question's name is "www" + pointer to "example.com" at offset 12.
	msg := buildQuery(1, question{"example.com", 1, 1})
	msg[5] = 2
	msg = append(msg, 3, 'w', 'w', 'w', 0xC0, 12, 0, 5, 0, 1)
	qs, err := parseQuery(msg)
	if err != nil {
		t.Fatal(err)
	}
	if qs[1].Name != "www.example.com" || typeString(qs[1].Type) != "CNAME" {
		t.Fatalf("got %+v", qs[1])
	}
}

func TestHealthzNotLogged(t *testing.T) {
	h, logs := testHandler()
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/healthz", nil))
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d", rec.Code)
	}
	if logs.Len() != 0 {
		t.Errorf("healthz was logged: %s", logs)
	}
}
