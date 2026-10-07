"use client";

import Link from "next/link";
import { LanguageToggle } from "@/components/language-toggle";
import { useLanguage } from "@/components/language-provider";

const vi = {
  title: "Bản quyền & mã nguồn mở",
  intro: "Trang này phân biệt rõ phần thuộc bản quyền POWER-AI-WEB với các thư viện mã nguồn mở và học liệu của bên thứ ba.",
  sections: [
    ["Bản quyền POWER-AI-WEB", "© 2026 Trần Thanh Duy. All rights reserved. Trừ khi được ghi rõ khác đi, mã nguồn gốc, giao diện, triển khai quy trình POWER, cấu trúc dữ liệu, tài liệu và học liệu do POWER-AI-WEB tự xây dựng được bảo hộ bản quyền. Việc repository được công khai trên GitHub không tự động đồng nghĩa với việc toàn bộ dự án được cấp giấy phép mã nguồn mở."],
    ["Mã nguồn công khai không đồng nghĩa mã nguồn mở", "Người dùng chỉ nhận các quyền mà một giấy phép cụ thể cấp rõ ràng. Nếu một file hoặc thành phần không ghi giấy phép mã nguồn mở, không được hiểu rằng có quyền sao chép, sửa đổi, phân phối, bán lại hoặc vận hành một dịch vụ thương mại phái sinh từ phần mã độc quyền của POWER-AI-WEB."],
    ["Thư viện mã nguồn mở", "POWER-AI-WEB sử dụng nhiều thư viện mã nguồn mở. Mỗi thư viện giữ nguyên giấy phép của chính nó. Ví dụ: Next.js và React dùng MIT; Firebase JavaScript SDK dùng Apache-2.0; FastAPI dùng MIT; OpenAI Python SDK dùng Apache-2.0. Các giấy phép này áp dụng cho chính các thành phần tương ứng, không tự động cấp quyền đối với mã hoặc thương hiệu POWER-AI-WEB."],
    ["Lưu ý đặc biệt về PyMuPDF / MuPDF", "Pipeline xử lý PDF hiện có sử dụng PyMuPDF. Thành phần này được cung cấp theo AGPL hoặc giấy phép thương mại. Vì vậy, trước khi vận hành POWER-AI-WEB như một SaaS mã nguồn đóng hoặc phân phối dưới dạng phần mềm độc quyền, dự án phải bảo đảm tuân thủ AGPL, mua giấy phép thương mại phù hợp hoặc thay thế dependency này bằng một giải pháp có giấy phép tương thích. Đây là vấn đề cần giải quyết trước khi thương mại hóa."],
    ["Học liệu và nội dung bên thứ ba", "SGK, bản scan, hình của nhà xuất bản, Campbell Biology và các nguồn học tập khác không trở thành tài sản mã nguồn mở chỉ vì được dùng làm nguồn tham khảo hoặc RAG. Bản quyền vẫn thuộc về chủ sở hữu tương ứng. POWER-AI-WEB không cấp quyền sao chép hoặc tái phân phối các tài liệu đó."],
    ["Nội dung do AI tạo", "Văn bản, câu hỏi và hình minh họa do AI tạo có thể chứa sai sót. Người học cần kiểm chứng với SGK và nguồn học liệu đáng tin cậy. Nội dung AI không phải là bản sao chính thức của SGK và không thay thế nguồn xuất bản gốc."],
    ["Dữ liệu và quyền riêng tư", "Dữ liệu người học, lịch sử học tập, mastery, dữ liệu phân tích, cơ sở dữ liệu production, khóa API, secrets và nguồn tài liệu riêng tư không được cấp phép cho việc tái sử dụng công khai."],
    ["Tên và thương hiệu", "Tên POWER-AI-WEB, POWER AI, logo và nhận diện sản phẩm không được cấp quyền sử dụng chỉ vì phần mềm có sử dụng các thư viện mã nguồn mở."],
  ],
  note: "Thông tin trên nhằm làm rõ mô hình cấp phép của dự án và không thay thế tư vấn pháp lý chuyên nghiệp cho một đợt phát hành thương mại cụ thể.",
  back: "Quay lại hướng dẫn sử dụng"
};

const en = {
  title: "Copyright & open-source notices",
  intro: "This page distinguishes POWER-AI-WEB proprietary materials from open-source dependencies and third-party educational content.",
  sections: [
    ["POWER-AI-WEB copyright", "© 2026 Trần Thanh Duy. All rights reserved. Unless expressly stated otherwise, original source code, interface design, POWER workflow implementation, data structures, documentation, and original educational materials created for POWER-AI-WEB are protected proprietary materials. A publicly visible GitHub repository does not by itself make the entire project open source."],
    ["Source-visible is not automatically open source", "Users receive only the rights expressly granted by an applicable license. If a file or component does not state an open-source license, public visibility should not be interpreted as permission to copy, modify, redistribute, resell, or operate a derivative commercial service from proprietary POWER-AI-WEB code."],
    ["Open-source dependencies", "POWER-AI-WEB uses open-source software under each component's own license. Examples include Next.js and React under MIT, Firebase JavaScript SDK under Apache-2.0, FastAPI under MIT, and the OpenAI Python SDK under Apache-2.0. Those licenses cover the corresponding upstream components and do not automatically license POWER-AI-WEB code or branding."],
    ["Special note on PyMuPDF / MuPDF", "The current PDF pipeline uses PyMuPDF. It is available under AGPL terms or a commercial license. Before operating POWER-AI-WEB as closed-source SaaS or distributing it as proprietary software, the project must comply with the applicable AGPL obligations, obtain an appropriate commercial license, or replace this dependency with a license-compatible alternative. This must be resolved before commercialization."],
    ["Educational and third-party content", "Textbooks, scans, publisher figures, Campbell Biology materials, and other learning sources do not become open source because they are used as references or RAG sources. Copyright remains with the respective owners. POWER-AI-WEB does not grant a right to copy or redistribute those materials."],
    ["AI-generated content", "AI-generated explanations, questions, and illustrations may contain errors. Learners should verify them against textbooks and reliable sources. AI output is not an official reproduction of a textbook and does not replace the original publication."],
    ["Data and privacy", "Learner data, study history, mastery data, analytics, production databases, API keys, secrets, and private source files are not licensed for public reuse."],
    ["Product name and branding", "The POWER-AI-WEB / POWER AI names, logos, and product identity are not licensed for reuse merely because the application incorporates open-source dependencies."],
  ],
  note: "This notice explains the project's current licensing model and is not a substitute for professional legal review of a specific commercial release.",
  back: "Back to the user guide"
};

export default function LegalPage() {
  const { language } = useLanguage();
  const t = language === "vi" ? vi : en;

  return (
    <div className="legal-public-shell">
      <header className="legal-public-header">
        <Link className="brand" href="/login">
          <span className="brand-mark">P</span>
          <span>POWER-AI-WEB</span>
        </Link>
        <LanguageToggle />
      </header>

      <main className="legal-public-main">
        <div className="page-heading">
          <div>
            <p className="eyebrow">POWER · LEGAL</p>
            <h1>{t.title}</h1>
          </div>
        </div>

        <section className="card legal-intro">
          <p>{t.intro}</p>
        </section>

        <div className="legal-grid">
          {t.sections.map(([title, body]) => (
            <section className="card legal-card" key={title}>
              <h2>{title}</h2>
              <p>{body}</p>
            </section>
          ))}
        </div>

        <section className="legal-note">
          <strong>{language === "vi" ? "Lưu ý" : "Note"}</strong>
          <p>{t.note}</p>
        </section>

        <p>
          <Link className="button secondary inline" href="/login">
            {language === "vi" ? "Về trang đăng nhập" : "Back to sign in"}
          </Link>
        </p>
      </main>

      <footer className="site-footer">
        <div>
          <strong>POWER-AI-WEB</strong>
          <span>© 2026 Trần Thanh Duy. All rights reserved.</span>
        </div>
      </footer>
    </div>
  );
}
