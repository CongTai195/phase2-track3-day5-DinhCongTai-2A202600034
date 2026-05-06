# Hệ Thống Nghiên Cứu Đa Tác Tử (Multi-Agent Research System)

Repository này chứa bản triển khai hoàn chỉnh của Hệ Thống Nghiên Cứu Đa Tác Tử được xây dựng bằng LangGraph. Hệ thống bao gồm một Supervisor đóng vai trò điều phối các tác vụ đến các đặc vụ chuyên biệt (Researcher, Analyst, Writer và Critic) để trả lời các câu hỏi phức tạp. Ngoài ra, dự án còn tích hợp sẵn công cụ benchmark để so sánh hiệu suất giữa hệ thống đa tác tử (multi-agent) và hệ thống đơn tác tử (single-agent) cơ bản.

## Kiến trúc hệ thống

```text
User Query
   |
   v
Supervisor / Router
   |------> Researcher Agent  -> tìm kiếm tài liệu & ghi chú
   |------> Analyst Agent     -> tạo bản phân tích có cấu trúc
   |------> Writer Agent      -> tổng hợp câu trả lời cuối cùng
   |------> Critic Agent      -> kiểm chứng sự thật & chấm điểm độ chính xác
   |
   v
Final Answer + Traces (LangSmith)
```

## Các tính năng chính

- **Điều phối Đa Tác Tử (Multi-Agent Orchestration)**: Sử dụng `StateGraph` của LangGraph để định tuyến có điều kiện.
- **Tìm kiếm Wikipedia**: Tích hợp client tìm kiếm Wikipedia không phụ thuộc thư viện ngoài (zero-dependency) để lấy dữ liệu thời gian thực.
- **Dữ liệu đầu ra có cấu trúc (Structured Outputs)**: Sử dụng OpenAI `gpt-4o-mini` kết hợp với Pydantic để đưa ra các quyết định điều phối đáng tin cậy.
- **Khả năng quan sát (Observability)**: Tích hợp với LangSmith để theo dõi luồng thực thi (tracing) và phân tích chi phí một cách chi tiết.
- **Đánh giá hiệu suất (Benchmarking)**: Tích hợp sẵn công cụ đánh giá để so sánh độ trễ (latency), chi phí (cost) và chất lượng (quality) so với baseline.

## Hướng dẫn cài đặt nhanh (Quickstart)

### 1. Thiết lập môi trường

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e "[dev]"
```

### 2. Cấu hình API Keys

Sao chép file `.env.example` thành `.env` và thiết lập các thông số:

```bash
OPENAI_API_KEY=your_openai_api_key
LANGSMITH_API_KEY=your_langsmith_api_key
```

### 3. Chạy Hệ Thống Đa Tác Tử

```bash
python3 -m multi_agent_research_lab.cli multi-agent --query "What is GraphRAG and how does it compare to standard RAG?"
```

## Sản phẩm bàn giao (Deliverables & Submission)

### 1. Báo cáo Benchmark
Vui lòng xem file `reports/benchmark_report.md` để xem kết quả so sánh hiệu suất giữa baseline Single-Agent và hệ thống Multi-Agent. Hệ thống Multi-Agent thể hiện chất lượng và chiều sâu tốt hơn nhờ các giai đoạn nghiên cứu và phân tích được cấu trúc rõ ràng.

### 2. Theo dõi luồng thực thi (Tracing)
Hệ thống được tích hợp hoàn toàn với **LangSmith** để tăng khả năng quan sát. Workflow sẽ ghi lại toàn bộ quá trình thực thi của từng tác tử, các quyết định điều phối, số lượng token sử dụng và chi phí. Thêm vào đó, `CriticAgent` sẽ đánh giá câu trả lời cuối cùng và ghi lại lời nhận xét trực tiếp vào thuộc tính span của LangSmith.

### 3. Các lỗi thường gặp và Cách khắc phục (Failure Modes & Fixes)
- **Vòng lặp điều phối vô hạn (Infinite Routing Loop)**: 
  - *Lỗi gặp phải*: Supervisor có thể liên tục định tuyến lặp lại giữa các tác tử nếu trạng thái hệ thống không có tiến triển.
  - *Cách khắc phục*: Đã triển khai rào chắn (guardrail) `max_iterations` trong Supervisor để buộc kết thúc sớm (chuyển hướng về `done`) nếu số lần lặp vượt quá giới hạn.
- **Ảo giác AI (Hallucinations)**: 
  - *Lỗi gặp phải*: Writer có thể tự bịa ra các dữ kiện không có trong ghi chú nghiên cứu, đặc biệt là với các chủ đề phức tạp.
  - *Cách khắc phục*: Bổ sung thêm `CriticAgent` để đối chiếu câu trả lời cuối cùng với các ghi chú thô, từ đó đưa ra điểm số về độ chính xác và mức độ ảo giác.
- **Vượt quá giới hạn Context (Context Length Exceeded)**: 
  - *Lỗi gặp phải*: Việc trả về quá nhiều tài liệu nguồn thô từ kết quả tìm kiếm có thể làm phình to context và vượt quá giới hạn độ dài của LLM.
  - *Cách khắc phục*: `ResearcherAgent` sẽ ngay lập tức tổng hợp các tài liệu thô thành các `research_notes` ngắn gọn trước khi chuyển trạng thái đi tiếp, giúp ngăn chặn tình trạng phình to context.