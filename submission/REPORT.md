# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Dương Thị Hồng Viên
- **MSSV:** 2A202602385
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/hviennduongne/K4-L3-DAY13-DuongThiHongVien-02385-Monitoring-LLMOps
- **Commit SHA cuối:** Chưa chốt — điền SHA sau khi tạo và push commit nộp cuối.
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-02385`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.txt` |
| Log validator | `evidence/02-log-validator.txt` |
| Dashboard validator | `evidence/03-dashboard-validator.txt` |
| Structured log | `evidence/04-structured-log.txt` |
| PII redaction | `evidence/05-pii-redaction.txt` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png`, `evidence/08b-trace-prompt-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.txt` |
| Incident log | `evidence/13-incident-log.txt` |
| Incident trace | `evidence/14-incident-trace.png` (trace `10014399a6937e4ae478cf5872c05b35`) |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100; 23 records; 20 thiếu required fields; 20 thiếu enrichment; 0 correlation ID | 100/100; 98 records; 0 thiếu required/enrichment; 47 correlation IDs | Chưa đạt ở baseline là kết quả dự kiến trước CP1. |
| `validate_dashboard.py` | HỢP LỆ: 6/6 panel | HỢP LỆ: 6/6 panel | Dashboard runtime tại `/dashboard` đọc trực tiếp `data/logs.jsonl`. |
| `pytest` | 22 passed in 2.86s (chạy với `--basetemp=.pytest_baseline_tmp`) | 26 passed in 2.68s | `pytest.ini` chuyển `basetemp` vào workspace nên lệnh chuẩn `python -m pytest -q` chạy được trên Windows. |
| Số traces hợp lệ | Chưa xác nhận trên Langfuse UI | 59 | Đã xác nhận trực tiếp trên Langfuse UI trong project `day13-k4-l3a-02385`; evidence hiển thị nhiều hơn mức tối thiểu 10 traces. |
| Số PII leak | 0 potential leaks | 0 potential leaks | Đã kiểm chứng end-to-end với email, điện thoại Việt Nam, CCCD và thẻ giả lập. |
| Latency P95 / TTFT P95 | | 2661 ms / 52 ms | Dashboard 60 phút sau workload CP2/CP3. |
| Retrieval success rate | | 100% | 0% request error trong cùng cửa sổ. |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware xóa contextvars ở đầu mỗi request, giữ `x-request-id` do client gửi hoặc sinh `req-<8-hex>`, bind vào structlog và trả lại qua response header cùng `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model`, `env`; `user_id` chỉ xuất hiện dưới dạng SHA-256 rút gọn 12 ký tự.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor `scrub_event` scrub đệ quy mọi chuỗi và được đặt trước `JsonlFileProcessor` lẫn `JSONRenderer`; các pattern xử lý email, số điện thoại Việt Nam, CCCD và thẻ thanh toán.
- **Cách kiểm chứng kết quả:** Xóa log baseline, chạy lại workload và một request có bốn loại PII giả lập. Response giữ `x-request-id: req-deadbeef`; log chỉ còn marker `[REDACTED_*]`; validator đạt 100/100 với 0 PII leak.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Xác thực API key trả project `day13-k4-l3a-02385`; chạy workload local và đọc lại root observations bằng Langfuse Observations API v2. Root có user ID hash, session, environment, feature/model tags và correlation ID.
- **Cấu trúc root/retrieval/generation observations:** Root `lab-agent-run` loại agent có hai child cùng parent ID: `retrieval` loại retriever và `fake-llm-generation` loại generation. Generation ghi model, managed prompt, usage input/output/total và total cost; không capture raw input/output.
- **Cách nối trace với log:** Lọc trace metadata theo `correlation_id`; ví dụ `req-7bd4d9c4` nối tới trace `123f2da3adcfc7e74a8a2c4388468177`.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** v1, labels `baseline` và (sau rollback) `production`.
- **Version/label candidate:** v2, label `candidate`.
- **Trace ID của mỗi version:** baseline v1 `c94e10f39088b2a061f286784e34589b`; candidate v2 `96f4c4add743ea9b6fa8fc4672faa33a`; production v2 `c653ea569b6f8d2b30436ed794477ac8`; production sau rollback v1 `d2e633b8458b69d2e0a29c1f5bc7262e`.
- **Cách promote và rollback `production`:** `scripts/manage_prompts.py promote` chuyển label sang v2 và tạo trace production v2; `rollback` chuyển lại v1. Trạng thái cuối: v1=`baseline,production`; v2=`candidate` (ngoài label hệ thống `latest`).

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** `/dashboard` đọc log 60 phút gần nhất, refresh 30 giây và hiển thị đúng latency/TTFT, traffic, errors/retrieval, cost, tokens và quality; mỗi panel có đơn vị và threshold/SLO.
- **Cấu hình liên quan:** [`config/dashboard.yaml`](../config/dashboard.yaml), [`config/slo.yaml`](../config/slo.yaml), [`config/alert_rules.yaml`](../config/alert_rules.yaml) và [`docs/alerts.md`](../docs/alerts.md).
- **SLO và lý do chọn:** 99.5% request trong cửa sổ 28 ngày phải có `response_sent` với latency ≤3000 ms; ngưỡng bảo vệ tail latency và phù hợp baseline sau warm-up.
- **Cách tính error budget:** 0.5% bad events; quy đổi theo thời gian là `28 × 24 × 60 × 0.005 = 201.6 phút`, hoặc `floor(total_requests × 0.005)` bad requests trong cửa sổ.
- **Ba alert và runbook tương ứng:** P95 latency >3000 ms/10m (critical), error rate >2%/5m (critical), mean quality <0.75/15m (warning); đều gửi Slack `#llmops-alerts`, có owner và runbook trong `docs/alerts.md`.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1` (cohort K4).
- **Khoảng thời gian điều tra:** 2026-09-29 08:38:56–08:39:10 UTC (5 requests/5 responses của feature `monitoring`).
- **Triệu chứng từ metrics:** Trong cửa sổ challenge, latency P50 = 2653 ms, P95/P99 = 2658 ms; cả 5/5 request vượt ngưỡng challenge 2000 ms. TTFT tối đa chỉ 50 ms và không có error, cho thấy latency xấu nhưng LLM first-token và availability bình thường.
- **Log line và correlation ID liên quan:** `data/logs.jsonl` dòng 88–89, correlation ID `req-7669f141`; `response_sent` có `latency_ms=2658`, `ttft_ms=50`, `feature=monitoring`, `tool_name=retrieval`, `tool_success=true`.
- **Trace ID và span gây ảnh hưởng:** Trace `10014399a6937e4ae478cf5872c05b35`; root agent 2.668 s, child retrieval 2.502 s, child generation 0.153 s. Hai child cùng parent, cùng correlation ID và status `DEFAULT`; retrieval chiếm gần toàn bộ duration.
- **Root cause:** Incident `rag_slow` làm bước retrieval chậm khoảng 2.5 giây. Metric vượt ngưỡng, log của `req-7669f141` và retrieval span trong trace đều chỉ về cùng bottleneck; generation không phải nguyên nhân.
- **Fix action:** Tắt incident (đã xác nhận `/health` trả `rag_slow=false`); với production, đặt timeout/circuit breaker cho retriever, fallback sang nguồn dữ liệu/cached result ổn định và không retry đồng loạt.
- **Preventive measure:** Theo dõi retrieval duration/success riêng, alert latency theo ngưỡng 2000 ms của challenge, load-test dependency trước deploy và giữ correlation ID để tự động nối metric → log → trace.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Scrub toàn bộ cấu trúc event theo kiểu đệ quy thay vì chỉ scrub `payload` cấp một, để PII trong metadata/list/dict lồng nhau cũng bị loại trước mọi file writer hoặc JSON renderer.
- **Một lỗi/blocker đã gặp:** Pytest ban đầu có 4 lỗi setup do quyền truy cập thư mục temp của Windows; lần kiểm tra Langfuse UI đầu tiên cũng dừng ở trạng thái tải vì chưa có phiên đăng nhập.
- **Cách tìm nguyên nhân và xử lý:** Baseline pytest gặp `PermissionError: [WinError 5]` khi truy cập `C:\Users\ACER\AppData\Local\Temp\pytest-of-ACER`; cấu hình `pytest.ini` chuyển `basetemp` vào workspace. Sau khi đăng nhập Langfuse Cloud, đã xác nhận trực tiếp 59 traces, waterfall, metadata và trạng thái prompt rollback trong đúng project cá nhân.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics dùng để phát hiện triệu chứng và khoanh time range; structured log trong khoảng đó cung cấp request cụ thể qua `correlation_id`; trace có cùng ID tách duration/status theo span để xác định bottleneck. Trong challenge, P95 vượt 2000 ms dẫn tới log `req-7669f141`, rồi trace xác nhận retrieval 2.502 s trong khi generation chỉ 0.153 s.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt version và label giúp truy vết chính xác hành vi đang chạy, so candidate với baseline và rollback production mà không sửa source. Token/cost cho biết tác động tài nguyên của generation; SLO/error budget biến latency/availability thành mục tiêu đo được và quyết định khi nào cần alert hoặc dừng rollout.
- **Điều quan trọng nhất đã học:** Một dashboard chỉ phát hiện triệu chứng; muốn kết luận root cause phải giữ metadata nhất quán và nối được metric, log, trace và prompt version của cùng request.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Evidence kỹ thuật và UI đã hoàn tất; còn tạo/push commit nộp cuối, lấy SHA và nộp URL/SHA trên LMS/Codelabs.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
