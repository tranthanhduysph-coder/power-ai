"use client";

import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { useLanguage } from "@/components/language-provider";

const vi = {
 title:"Hướng dẫn sử dụng POWER-AI-WEB", intro:"POWER giúp bạn tự học Sinh học theo một chu trình có mục tiêu, kế hoạch, luyện tập, đánh giá và điều chỉnh. Bạn là người chủ động học; AI hỗ trợ giải thích và gợi mở.",
 steps:[
  ["P · PREPARE — Xác định mục tiêu","Chọn bài học và viết mục tiêu SMART: cụ thể, đo lường được, có thể đạt được, phù hợp và có thời hạn.","Ví dụ: Trong 30 phút, giải thích được ba dạng đột biến gene và phân biệt bằng ví dụ.","Chuyển pha khi mục tiêu học tập đã rõ."],
  ["O · ORGANIZE — Lập kế hoạch","Chọn nội dung, nguồn học, hoạt động và phân bổ thời gian.","Ví dụ: 10 phút ôn khái niệm, 15 phút phân tích ví dụ, 10 phút luyện câu hỏi.","Chuyển pha khi đã có kế hoạch khả thi."],
  ["W · WORK — Thực hiện việc học","Đọc tài liệu, tự giải thích, đối chiếu bằng chứng và trao đổi với Biology AI. Hãy tự trả lời trước khi xem gợi ý.","Ví dụ: giải thích vì sao DNA polymerase tổng hợp mạch mới theo chiều 5′ → 3′.","Chuyển pha sau khi có sản phẩm học tập hoặc minh chứng đã hiểu."],
  ["E · EVALUATE — Tự đánh giá","Làm bài đánh giá gắn với chu trình POWER; xem câu sai, lời giải thích và khái niệm cần ôn.","Ví dụ: hoàn thành bài kiểm tra gồm trắc nghiệm, đúng/sai và trả lời ngắn.","Khi hoàn thành bài đánh giá, hệ thống có thể chuyển sang RETHINK."],
  ["R · RETHINK — Phản tư và điều chỉnh","Nhìn lại mục tiêu, lỗi sai, chiến lược học và xác định bước học tiếp theo.","Ví dụ: nhận ra mình nhầm mạch dẫn đầu và mạch gián đoạn, rồi lập kế hoạch ôn lại.","Hoàn tất chu trình khi đã ghi nhận điều học được và cách cải thiện."]
 ],
 other:[
  ["Bắt đầu học","Đăng nhập bằng Google hoặc email/mật khẩu → vào Học → chọn lớp và bài có sẵn → thực hiện tuần tự các pha. Có thể xem lại pha đã hoàn thành mà không phải khởi động chu trình mới."],
  ["Luyện tập","Vào Luyện tập. Phù hợp với tôi chọn bài dựa trên dữ liệu mastery hiện có; Tự chọn cho phép đặt mức khó, số câu và dạng câu; Tạo bài luyện bằng AI tạo bộ câu hỏi theo yêu cầu. Ba dạng gồm trắc nghiệm, đúng/sai và trả lời ngắn. Bài luyện AI độc lập không cập nhật mastery và không dùng làm minh chứng POWER Evaluate."],
  ["Theo dõi tiến trình","Vào Tiến trình để xem các kết quả và khái niệm cần củng cố; dùng phản hồi này để điều chỉnh kế hoạch học."],
  ["Khi nào tạo được hình minh họa?","Trong trang Học, mở Biology AI và nhập yêu cầu hình rõ ràng về một cấu trúc hoặc cơ chế Sinh học. Tính năng chỉ có thể tạo hình khi truy xuất được đoạn học liệu phù hợp đã có trong hệ thống, đồng thời dịch vụ tạo hình AI được cấu hình và hoạt động. Nếu bài chưa có học liệu nền được lập chỉ mục, yêu cầu có thể bị từ chối (422). Hãy thử bài có học liệu hoặc nội dung sát với tài liệu đang học. Hình AI chỉ là minh họa, cần kiểm tra lại các chi tiết khoa học bằng SGK."],
  ["Lưu ý khi dùng AI","AI có thể sai. Hãy kiểm chứng định nghĩa, số liệu, sơ đồ và lời giải với SGK Sinh học 10–12 Kết nối tri thức và nguồn học liệu được dẫn. Không chia sẻ mật khẩu hoặc thông tin riêng tư trong hội thoại."],
  ["Bản quyền & mã nguồn mở","POWER-AI-WEB có phần mã nguồn và nội dung do dự án sở hữu, đồng thời sử dụng các thư viện mã nguồn mở theo giấy phép riêng của từng thư viện. Việc repository công khai không đồng nghĩa toàn bộ dự án là mã nguồn mở. Xem trang Bản quyền & mã nguồn mở ở cuối ứng dụng để biết chi tiết."]
 ]};
const en={
 title:"POWER-AI-WEB user guide",intro:"POWER supports self-directed Biology learning through a cycle of setting goals, planning, working, evaluating and reflecting. You lead your learning; AI provides explanations and guidance.",
 steps:[
 ["P · PREPARE — Set a goal","Choose a lesson and make a SMART goal: Specific, Measurable, Achievable, Relevant and Time-bound.","Example: In 30 minutes, explain three types of gene mutations with examples.","Continue when the goal is clear."],
 ["O · ORGANIZE — Plan","Choose resources, learning tasks and timing.","Example: 10 minutes review, 15 minutes examples, 10 minutes practice.","Continue when you have a realistic plan."],
 ["W · WORK — Learn","Read, explain concepts in your own words and discuss evidence with Biology AI. Try answering before requesting hints.","Example: explain why DNA polymerase synthesizes in the 5′ → 3′ direction.","Continue when you have evidence of understanding."],
 ["E · EVALUATE — Check understanding","Complete the assessment linked to the POWER cycle and review wrong answers and weak concepts.","Example: attempt multiple-choice, true/false and short-answer items.","A completed assessment may advance the cycle to RETHINK."],
 ["R · RETHINK — Reflect and revise","Review goals, errors and strategies, then decide what to improve.","Example: revisit leading and lagging strand synthesis after confusing them.","Finish by recording what you learned and your next action."]
 ],
 other:[
 ["Start learning","Sign in with Google or email/password → Learn → select a ready lesson → follow the POWER phases. You can revisit completed phases."],
 ["Practice","Recommended for me adapts to available mastery evidence. Custom lets you choose difficulty, length and formats. AI-generated practice creates on-demand questions. Available formats: multiple choice, true/false, short answer. Standalone AI practice does not update mastery or count as POWER Evaluate evidence."],
 ["Progress","Open Progress to review results and concepts that need more practice."],
 ["When can AI generate an illustration?","In Learn, ask Biology AI for a clear illustration of a Biology mechanism or structure. Image generation requires relevant indexed source passages to be retrieved and a configured, working AI image service. A lesson without grounded source content may return error 422. Try a lesson with available material or a prompt closer to the indexed text. Verify scientific accuracy against the textbook."],
 ["Use AI responsibly","AI can make mistakes. Check definitions, diagrams and answers against the KNTT Biology 10–12 textbooks and cited learning resources. Do not share passwords or private information."],
  ["Copyright & open source","POWER-AI-WEB contains proprietary project materials and also uses open-source libraries under their own licenses. A public repository does not automatically make the entire project open source. See the Copyright & open source page in the application footer for details."]
 ]};
export default function HelpPage() {
 const {language}=useLanguage();
 const t=language==="vi"?vi:en;
 return <AuthGuard><AppShell><div className="page-heading"><div><p className="eyebrow">POWER · GUIDE</p><h1>{t.title}</h1></div></div>
 <section className="card" style={{padding:"24px",marginBottom:"22px"}}><p style={{fontSize:"1.08rem",lineHeight:1.75,margin:0}}>{t.intro}</p></section>
 <h2>{language==="vi"?"Năm pha POWER":"The five POWER phases"}</h2>
 <div style={{display:"grid",gap:"14px"}}>{t.steps.map(([name,desc,example,gate])=><section className="card" key={name} style={{padding:"20px 24px"}}><h3 style={{marginTop:0}}>{name}</h3><p>{desc}</p><p className="muted"><strong>{language==="vi"?"Ví dụ":"Example"}:</strong> {example.replace(/^Ví dụ: |^Example: /,"")}</p><p><strong>{language==="vi"?"Điều kiện chuyển pha":"Continue when"}:</strong> {gate}</p></section>)}</div>
 <h2 style={{marginTop:"30px"}}>{language==="vi"?"Các chức năng và điều kiện sử dụng":"Features and requirements"}</h2>
 <div style={{display:"grid",gap:"14px"}}>{t.other.map(([name,detail])=><section className="card" key={name} style={{padding:"20px 24px"}}><h3 style={{marginTop:0}}>{name}</h3><p style={{lineHeight:1.7,marginBottom:0}}>{detail}</p></section>)}</div>
 <p style={{marginTop:"25px"}}><Link className="button primary inline" href="/learn">{language==="vi"?"Bắt đầu học →":"Start learning →"}</Link></p>
 </AppShell></AuthGuard>;
}
