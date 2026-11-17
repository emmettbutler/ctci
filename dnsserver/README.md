# dnsquery

A small HTTP service that accepts a base64-encoded DNS query
([RFC 1035](https://www.rfc-editor.org/rfc/rfc1035)) and returns its question
section as JSON.

## Quickstart With Docker

The image is a two-stage build: a static binary on
`gcr.io/distroless/static-debian12:nonroot`. It is about 15 MB, has no shell,
and runs as UID 65532.

```sh
docker build -t dnsquery:latest .
docker run --rm -p 8080:8080 --read-only dnsquery:latest
```

## API

### `POST /dns/queries`

The request body is a single DNS message in wire format, base64-encoded.
Both the standard and URL-safe alphabets are accepted, with or without
padding. Surrounding whitespace is ignored when decoding.

**Response** `200 OK`, `application/json`:

```json
{
  "id": "c79a744c20b0d745e93e4309b0d9a81d20db1a987790413553a936a423c52f7f",
  "questions": [{ "name": "example.com", "type": "A" }]
}
```

| Field              | Description                                                                                                                                                                                                           |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`               | Hex SHA-256 of the raw request body. Identical bodies always produce the same ID.                                                                                                                                     |
| `questions[].name` | Queried domain name, without the trailing dot (`.` for the root). Compression pointers are followed.                                                                                                                  |
| `questions[].type` | TYPE mnemonic from RFC 1035 §3.2.2 (`A`, `NS`, `CNAME`, `SOA`, `PTR`, `MX`, `TXT`, …) or a §3.2.3 QTYPE (`AXFR`, `MAILB`, `MAILA`, `*`). Types RFC 1035 doesn't define use the RFC 3597 form, e.g. `TYPE28` for AAAA. |

The `id` is computed from the exact bytes sent, before base64 decoding.
Encodings of the same message that differ, for example by a trailing newline
or padding, therefore get different IDs.

**Caching.** The response depends only on the request body, so the server sends the following:

- `ETag: "<id>"`
- `Cache-Control: public, max-age=31536000, immutable`

A request with an `If-None-Match` header that matches the ETag gets
`304 Not Modified` with no body. Shared HTTP caches generally don't store POST
responses, so in practice these headers mainly benefit clients that send
`If-None-Match`.

**Errors** are returned as JSON (`{"error": "..."}`) with `Cache-Control: no-store`:

| Status | Cause                                                                                                                                                                                                        |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `400`  | Body is not valid base64, the message is truncated or shorter than the 12-byte header, the message is a response (QR=1), or a name is malformed (pointer loop, longer than 255 octets, reserved label type). |
| `405`  | Any method other than POST on `/dns/queries`.                                                                                                                                                                |
| `413`  | Body larger than 128 KiB.                                                                                                                                                                                    |

### `GET /healthz`

Returns `200 OK` with an empty body. Used by the Kubernetes probes. It is not
written to the access log.

### Logging

The server writes JSON lines to STDOUT:

- `access` for every request except `/healthz`: method, path, remote
  address, user agent, status, duration.
- `dns query parsed`: the full JSON response for each successfully parsed query.

```json
{"time":"…","level":"INFO","msg":"dns query parsed","response":{"id":"c79a…2f7f","questions":[{"name":"example.com","type":"A"}]}}
{"time":"…","level":"INFO","msg":"access","method":"POST","path":"/dns/queries","remote":"127.0.0.1:50439","user_agent":"curl/8.7.1","status":200,"duration_ms":0}
```

## Configuration

| Flag    | Env var | Default | Description    |
| ------- | ------- | ------- | -------------- |
| `-addr` | `ADDR`  | `:8080` | Listen address |

The flag takes precedence over the environment variable. On SIGINT or
SIGTERM, the server stops accepting connections and lets in-flight requests
finish, waiting up to 10 seconds.

## Build and run locally

Requires Go 1.27+.

```sh
go test -race ./...
go run .                      # listens on :8080
go run . -addr 127.0.0.1:9000
```

Or build a binary:

```sh
go build -o dnsquery .
./dnsquery
```

## Docker

The image is a two-stage build: a static binary on
`gcr.io/distroless/static-debian12:nonroot`. It is about 15 MB, has no shell,
and runs as UID 65532.

```sh
docker build -t dnsquery:latest .
docker run --rm -p 8080:8080 --read-only dnsquery:latest
```

## Kubernetes

The manifests in `k8s/` are applied with Kustomize (`kubectl apply -k`):

| File                 | Resource                                                                                                                                          |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `namespace.yaml`     | `dnsquery` namespace, Pod Security `restricted` enforced                                                                                          |
| `deployment.yaml`    | 2 replicas, zero-downtime rolling update, `/healthz` readiness and liveness probes, non-root, read-only root filesystem, all capabilities dropped |
| `service.yaml`       | ClusterIP Service, port 80 → container port 8080                                                                                                  |
| `pdb.yaml`           | PodDisruptionBudget, `minAvailable: 1`                                                                                                            |
| `hpa.yaml`           | HorizontalPodAutoscaler, 2–10 replicas at 70% CPU (requires metrics-server)                                                                       |
| `kustomization.yaml` | Sets the namespace and image                                                                                                                      |

### Local testing with minikube

```sh
# Start minikube without changing your current kubectl context
minikube start --driver=docker --keep-context --kubernetes-version=stable
minikube addons enable metrics-server

# zsh/bash helper that pins every kubectl call to minikube
k() { kubectl --context=minikube "$@"; }

# Build the image locally and load it into the cluster (no registry needed)
docker build -t dnsquery:latest .
minikube image load dnsquery:latest

# Deploy
k apply -k k8s
k -n dnsquery rollout status deploy/dnsquery
k -n dnsquery get pods,svc,hpa

# Reach the Service from your machine
k -n dnsquery port-forward svc/dnsquery 8080:80
```

After rebuilding the image, reload it and restart the pods:

```sh
docker build -t dnsquery:latest . && minikube image load dnsquery:latest
k -n dnsquery rollout restart deploy/dnsquery
```

View logs:

```sh
k -n dnsquery logs -l app.kubernetes.io/name=dnsquery --prefix -f
```

Clean up:

```sh
k delete -k k8s     # remove the app
minikube stop       # stop the cluster (or: minikube delete)
```

## Example requests

The examples assume the server is reachable at `localhost:8080`, either via
`go run .`, `docker run -p 8080:8080 …`, or the minikube port-forward above.

### Single question: `example.com A`

This query also includes an EDNS OPT record in the additional section, which
the server ignores.

```sh
curl -X POST --data 'EjQBIAABAAAAAAABB2V4YW1wbGUDY29tAAABAAEAACkQAAAAAAAAAA==' \
  http://localhost:8080/dns/queries
```

```json
{
  "id": "c79a744c20b0d745e93e4309b0d9a81d20db1a987790413553a936a423c52f7f",
  "questions": [{ "name": "example.com", "type": "A" }]
}
```

### Multiple questions with name compression

`example.com MX`, plus `www.example.com AAAA`. The second name is encoded as
`www` followed by a compression pointer to `example.com`.

```sh
curl -X POST --data 'vu8BAAACAAAAAAAAB2V4YW1wbGUDY29tAAAPAAEDd3d3wAwAHAAB' \
  http://localhost:8080/dns/queries
```

```json
{
  "id": "c9be931e37499b4be8e812261cb3b31990333d4930ec86d9a3fde1ca4b3d304f",
  "questions": [
    { "name": "example.com", "type": "MX" },
    { "name": "www.example.com", "type": "TYPE28" }
  ]
}
```

### URL-safe base64 without padding: `example.org *` (ANY)

```sh
curl -X POST --data 'AAEBAAABAAAAAAAAB2V4YW1wbGUDb3JnAAD_AAE' \
  http://localhost:8080/dns/queries
```

```json
{
  "id": "1561daaa77bd94545afe4b6b9099a99ec845da8b365f7421d6562b68a8deb839",
  "questions": [{ "name": "example.org", "type": "*" }]
}
```

### Caching headers and conditional requests

```sh
curl -i -X POST --data 'EjQBIAABAAAAAAABB2V4YW1wbGUDY29tAAABAAEAACkQAAAAAAAAAA==' \
  http://localhost:8080/dns/queries
```

```http
HTTP/1.1 200 OK
Cache-Control: public, max-age=31536000, immutable
Content-Type: application/json
Etag: "c79a744c20b0d745e93e4309b0d9a81d20db1a987790413553a936a423c52f7f"
Content-Length: 122
```

Send the ETag back to get a `304`:

```sh
curl -i -X POST \
  -H 'If-None-Match: "c79a744c20b0d745e93e4309b0d9a81d20db1a987790413553a936a423c52f7f"' \
  --data 'EjQBIAABAAAAAAABB2V4YW1wbGUDY29tAAABAAEAACkQAAAAAAAAAA==' \
  http://localhost:8080/dns/queries
```

```http
HTTP/1.1 304 Not Modified
Cache-Control: public, max-age=31536000, immutable
Etag: "c79a744c20b0d745e93e4309b0d9a81d20db1a987790413553a936a423c52f7f"
```

### Building your own query

Write the wire-format message with `printf`, then base64-encode it. This
example is a 12-byte header (ID `0x1234`, RD set, one question) followed by
`example.com`, type A (1), class IN (1):

```sh
printf '\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01' \
  | base64 > query.b64

curl -X POST --data-binary @query.b64 http://localhost:8080/dns/queries
```

`--data-binary` sends the file unchanged, including the trailing newline that
`base64` adds. That newline is part of the body, so it changes the `id`.
`--data @file` strips newlines instead.

### Errors

```sh
curl -X POST --data 'not a dns query' http://localhost:8080/dns/queries
# 400 {"error":"request body is not valid base64"}

curl -X POST --data 'AAAA' http://localhost:8080/dns/queries
# 400 {"error":"invalid DNS query: message truncated"}

curl -i http://localhost:8080/dns/queries
# HTTP/1.1 405 Method Not Allowed
```

## Project layout

```
.
├── main.go          # HTTP server, handler, logging, caching headers
├── dns.go           # DNS header/question parser and TYPE mnemonics
├── main_test.go     # handler and parser tests
├── Dockerfile
├── .dockerignore
└── k8s/             # Kustomize manifests
```
