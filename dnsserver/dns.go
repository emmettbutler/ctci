package main

import (
	"encoding/binary"
	"errors"
	"fmt"
	"strconv"
	"strings"
)

// Reference implementations. "dnsmessage" is golang.org/x/net/dns/dnsmessage
// (also vendored in GOROOT/src/vendor), "miekg" is github.com/miekg/dns v1.1.62.
//
//   readName:
//     dnsmessage message.go (*Name).unpack, skipName
//     miekg      msg.go     UnpackDomainName
//   writeLabel:
//     dnsmessage has no equivalent; it rejects labels containing '.' instead
//     miekg      escaping is inline in UnpackDomainName, using
//                types.go isDomainNameLabelSpecial and escapeByte
//   parseQuery (header):
//     dnsmessage message.go (*header).unpack, (*Parser).Start
//     miekg      msg.go     unpackMsgHdr, (*Msg).unpack
//   parseQuery (questions):
//     dnsmessage message.go (*Parser).Question
//     miekg      msg.go     unpackQuestion
//   parseQuery (QR-bit check):
//     neither library rejects responses; the closest is net/dnsclient_unix.go
//     checkHeader in the standard library
//   typeString, typeNames:
//     dnsmessage message.go Type.String
//     miekg      defaults.go Type.String, ztypes.go TypeToString
//
// Differences: the pointer-hop limit is 10 in dnsmessage and 126 in miekg
// (maxCompressionPointers), versus maxPointerHops here. The 255-octet check
// matches miekg's budget check; dnsmessage limits the decoded name length
// (nonEncodedNameMax) instead.

const (
	headerLen      = 12
	maxPointerHops = 64
	maxNameLen     = 255
)

var (
	errTruncated     = errors.New("message truncated")
	errNotQuery      = errors.New("message is a response, not a query")
	errPointerLoop   = errors.New("too many compression pointers")
	errNameTooLong   = errors.New("domain name exceeds 255 octets")
	errReservedLabel = errors.New("reserved label type")
)

// typeNames maps TYPE values from RFC 1035 section 3.2.2, plus the QTYPE-only
// values from section 3.2.3, which may legitimately appear in a question.
var typeNames = map[uint16]string{
	1:   "A",
	2:   "NS",
	3:   "MD",
	4:   "MF",
	5:   "CNAME",
	6:   "SOA",
	7:   "MB",
	8:   "MG",
	9:   "MR",
	10:  "NULL",
	11:  "WKS",
	12:  "PTR",
	13:  "HINFO",
	14:  "MINFO",
	15:  "MX",
	16:  "TXT",
	252: "AXFR",
	253: "MAILB",
	254: "MAILA",
	255: "*",
}

// typeString returns the mnemonic for t, falling back to the generic
// "TYPEnnn" form from RFC 3597 for values RFC 1035 does not define.
func typeString(t uint16) string {
	if s, ok := typeNames[t]; ok {
		return s
	}
	return "TYPE" + strconv.Itoa(int(t))
}

type question struct {
	Name  string
	Type  uint16
	Class uint16
}

// parses the header and question section of a DNS message.
// The answer, authority and additional sections are ignored.
func parseQuery(msg []byte) ([]question, error) {
	if len(msg) < headerLen {
		return nil, errTruncated
	}
	flags := binary.BigEndian.Uint16(msg[2:4])
	if flags&0x8000 != 0 {
		return nil, errNotQuery
	}
	qdcount := int(binary.BigEndian.Uint16(msg[4:6]))

	questions := make([]question, 0, min(qdcount, 16))
	off := headerLen
	for i := 0; i < qdcount; i++ {
		name, next, err := readName(msg, off)
		if err != nil {
			return nil, fmt.Errorf("question %d: %w", i, err)
		}
		if next+4 > len(msg) {
			return nil, fmt.Errorf("question %d: %w", i, errTruncated)
		}
		questions = append(questions, question{
			Name:  name,
			Type:  binary.BigEndian.Uint16(msg[next : next+2]),
			Class: binary.BigEndian.Uint16(msg[next+2 : next+4]),
		})
		off = next + 4
	}
	return questions, nil
}

// readName decodes the domain name starting at off, following compression
// pointers (RFC 1035 section 4.1.4). It returns the name in presentation
// format without the trailing dot ("." for the root) and the offset just
// past the name in the original position.
func readName(msg []byte, off int) (string, int, error) {
	var (
		sb      strings.Builder
		wireLen = 1 // terminating zero octet
		hops    = 0
		end     = -1
	)
	for {
		if off >= len(msg) {
			return "", 0, errTruncated
		}
		l := int(msg[off])
		switch l & 0xC0 {
		case 0x00:
			if l == 0 {
				if end < 0 {
					end = off + 1
				}
				if sb.Len() == 0 {
					return ".", end, nil
				}
				return sb.String(), end, nil
			}
			if off+1+l > len(msg) {
				return "", 0, errTruncated
			}
			wireLen += l + 1
			if wireLen > maxNameLen {
				return "", 0, errNameTooLong
			}
			if sb.Len() > 0 {
				sb.WriteByte('.')
			}
			writeLabel(&sb, msg[off+1:off+1+l])
			off += 1 + l
		case 0xC0:
			if off+2 > len(msg) {
				return "", 0, errTruncated
			}
			if hops++; hops > maxPointerHops {
				return "", 0, errPointerLoop
			}
			if end < 0 {
				end = off + 2
			}
			off = int(binary.BigEndian.Uint16(msg[off:off+2]) & 0x3FFF)
		default:
			return "", 0, errReservedLabel
		}
	}
}

// writeLabel writes a label in presentation format, escaping dots,
// backslashes and non-printable octets (RFC 1035 section 5.1).
func writeLabel(sb *strings.Builder, label []byte) {
	for _, c := range label {
		switch {
		case c == '.' || c == '\\':
			sb.WriteByte('\\')
			sb.WriteByte(c)
		case c < 0x21 || c > 0x7E:
			fmt.Fprintf(sb, "\\%03d", c)
		default:
			sb.WriteByte(c)
		}
	}
}
