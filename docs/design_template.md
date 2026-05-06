# Design Template

## Problem

Hệ thống cần xử lý các câu hỏi nghiên cứu phức tạp từ người dùng, tìm kiếm thông tin từ các nguồn dữ liệu (như Wikipedia hoặc web), phân tích các thông tin đó để trích xuất các ý chính và bằng chứng, sau đó tổng hợp thành một câu trả lời hoàn chỉnh, rõ ràng, có trích dẫn nguồn.

## Why multi-agent?

Single-agent thường gặp khó khăn với các tác vụ yêu cầu nhiều bước logic và context window lớn. Khi gộp chung việc tìm kiếm, đọc hiểu, phân tích và viết vào một prompt duy nhất, mô hình dễ bị hallucination, quên context hoặc trả lời hời hợt. Multi-agent giải quyết vấn đề này bằng cách chia nhỏ tác vụ (separation of concerns), giúp mỗi agent tập trung vào một nhiệm vụ chuyên biệt, giảm tải cho từng agent và tăng độ chính xác của kết quả cuối cùng.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Điều phối các worker agent, quyết định agent nào chạy tiếp hoặc kết thúc. | Current `ResearchState` | Next route (e.g. `researcher`, `done`) | Chọn sai route dẫn đến loop vô hạn (đã có `max_iterations` guard). |
| Researcher | Tìm kiếm thông tin từ nguồn ngoài và ghi chép lại các thông tin thô. | Query, `max_sources` | `sources`, `research_notes` | Không tìm thấy nguồn, trả về mảng rỗng. |
| Analyst | Đọc các research notes, trích xuất claim chính và đánh giá bằng chứng. | `research_notes` | `analysis_notes` | Phân tích thiếu sót do context quá dài. |
| Writer | Tổng hợp notes thành câu trả lời cuối cùng theo format yêu cầu. | `research_notes`, `analysis_notes` | `final_answer` | Bịa thêm thông tin không có trong notes (hallucination). |

## Shared state

- `request`: Input từ người dùng (query, audience).
- `iteration`: Đếm số bước đã chạy để chống loop vô hạn.
- `route_history`: Lưu vết các quyết định điều phối của Supervisor.
- `sources`: Danh sách tài liệu thô tải về (SourceDocument).
- `research_notes`: Ghi chép thô từ Researcher.
- `analysis_notes`: Phân tích sâu từ Analyst.
- `final_answer`: Kết quả cuối cùng trả cho người dùng từ Writer.
- `trace`: Lưu lại các sự kiện, cost, token usage cho Observability.

## Routing policy

Graph bao gồm 1 node Supervisor làm router và 3 node worker. Supervisor luôn là điểm bắt đầu và điểm hội tụ sau mỗi worker:
`Supervisor -> (Researcher | Analyst | Writer | END)`
- Nếu chưa có sources -> Gọi Researcher.
- Nếu đã có sources nhưng chưa có analysis -> Gọi Analyst.
- Nếu đã có analysis nhưng chưa có final_answer -> Gọi Writer.
- Nếu đã có final_answer hợp lệ -> END.

## Guardrails

- Max iterations: Cấu hình `max_iterations = 6` trong state/supervisor. Nếu vượt quá sẽ ép `done`.
- Timeout: Timeout ở level LLM client (nếu có).
- Retry: Retries ở mức API calls (sử dụng `tenacity` trong LLMClient).
- Fallback: Nếu agent fail hoặc supervisor trả về route không hợp lệ, hệ thống sẽ fallback về "done".
- Validation: Supervisor sử dụng Structured Outputs (`pydantic`) để đảm bảo LLM trả về đúng định dạng route.

## Benchmark plan

- **Query**: "What is GraphRAG and how does it compare to standard RAG?"
- **Metric**: Latency (giây), Cost (USD), Quality (0-10, đo bằng LLM-as-a-judge).
- **Expected outcome**: Multi-agent chậm hơn và tốn kém hơn Single-agent baseline, nhưng điểm Quality phải cao hơn đáng kể do có dẫn chứng và phân tích sâu sắc hơn.

## Exit Ticket

1. **Case nào nên dùng multi-agent? Vì sao?**
   Nên dùng cho các quy trình làm việc phức tạp, tốn thời gian, yêu cầu nhiều kỹ năng hoặc các bước độc lập (như lập trình, nghiên cứu dài hạn, kiểm thử). Việc chia nhỏ giúp dễ debug, dễ tối ưu từng thành phần (ví dụ: dùng model nhỏ cho routing, model lớn cho writing) và giảm nguy cơ suy giảm chất lượng do prompt quá dài.
2. **Case nào không nên dùng multi-agent? Vì sao?**
   Không nên dùng cho các tác vụ đơn giản, deterministic (chỉ cần 1-2 bước) như dịch thuật cơ bản, classification text, hoặc tóm tắt một đoạn văn bản ngắn. Sử dụng multi-agent trong các trường hợp này chỉ làm tăng độ trễ (latency), chi phí (cost) và độ phức tạp của hệ thống mà không mang lại giá trị gia tăng nào.
