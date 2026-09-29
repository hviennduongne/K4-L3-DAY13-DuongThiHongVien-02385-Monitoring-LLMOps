# Alert runbooks

Các alert dưới đây dựa trên triệu chứng người dùng/SLO. Kênh thông báo chung là Slack `#llmops-alerts`.

## High request latency

- **Severity / duration:** critical, duy trì 10 phút.
- **Điều kiện:** P95 của `response_sent.latency_ms` lớn hơn 3000 ms.
- **SLI/SLO:** SLO `fast_successful_requests`; người dùng chờ lâu hoặc timeout.
- **Ba bước kiểm tra:** (1) xác định time range trên panel latency và so sánh TTFT; (2) lọc log chậm, lấy `correlation_id`; (3) mở trace tương ứng và so thời gian retrieval với generation.
- **Mitigation:** giảm concurrency/rate, tắt incident practice nếu đang bật, hoặc chuyển sang prompt/model ổn định đã biết trong khi điều tra span chậm.
- **Owner:** `llm-platform`.

## Elevated request error rate

- **Severity / duration:** critical, duy trì 5 phút.
- **Điều kiện:** `request_failed / request_received * 100 > 2%`.
- **SLI/SLO:** successful request ratio; người dùng nhận HTTP 5xx hoặc không có câu trả lời.
- **Ba bước kiểm tra:** (1) xem breakdown `error_type` và retrieval success; (2) lấy một correlation ID lỗi từ structured log; (3) kiểm tra trace/span lỗi và dependency liên quan.
- **Mitigation:** rollback thay đổi mới nhất, cô lập dependency lỗi, bật fallback an toàn và giới hạn retry để tránh khuếch đại tải.
- **Owner:** `api-oncall`.

## Quality degradation

- **Severity / duration:** warning, duy trì 15 phút.
- **Điều kiện:** trung bình `response_sent.quality_score` nhỏ hơn 0.75.
- **SLI/SLO:** quality guardrail; câu trả lời vẫn thành công kỹ thuật nhưng giảm độ hữu ích.
- **Ba bước kiểm tra:** (1) đối chiếu feature và prompt version của các request điểm thấp; (2) kiểm tra retrieval success và tài liệu trả về; (3) so trace candidate với baseline trên cùng input.
- **Mitigation:** rollback label `production` về prompt baseline, giữ lại trace IDs để phân tích và ngừng promote candidate cho tới khi quality phục hồi.
- **Owner:** `ai-quality`.
