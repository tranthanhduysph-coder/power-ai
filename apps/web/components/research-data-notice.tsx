import Link from "next/link";

const notices = {
  vi: {
    title: "Thu thập và sử dụng dữ liệu học tập",
    updated: "Cập nhật ngày 19/10/2026",
    paragraphs: [
      "POWER-AI-WEB ghi nhận dữ liệu hành vi học tập khi bạn sử dụng nền tảng: thời điểm và thời lượng hoạt động; thao tác và tiến độ qua các bước Prepare, Organize, Work, Evaluate, Rethink; số lượt làm bài, kết quả Practice/Evaluate và các chỉ số mức độ nắm vững kiến thức (mastery). Dữ liệu hành vi này chỉ được sử dụng cho nghiên cứu giáo dục và cải tiến sản phẩm, không được bán hoặc sử dụng cho quảng cáo.",
      "Phân tích có thể bao gồm các bản ghi lịch sử đã được hệ thống lưu, không phụ thuộc việc trả lời Google Form. Chỉ quản trị viên nghiên cứu được phân quyền mới có thể xuất dữ liệu. CSV hành vi sử dụng mã người tham gia thay cho tên và email, không chứa nội dung hội thoại hoặc câu trả lời tự do. Bảng đối chiếu email với mã người tham gia được quản lý riêng, chỉ dùng khi cần liên kết dữ liệu phục vụ hai mục đích trên; không công khai dữ liệu định danh học sinh.",
      "Để hỏi về dữ liệu của bạn hoặc yêu cầu xem xét, chỉnh sửa hay xóa dữ liệu, liên hệ ttduy@sgu.edu.vn.",
    ],
    summary: "Dữ liệu hành vi học tập, kể cả lịch sử đã lưu, được thu thập chỉ cho nghiên cứu giáo dục và cải tiến sản phẩm.",
    link: "Xem điều khoản về dữ liệu",
  },
  en: {
    title: "Collection and use of learning data",
    updated: "Updated 19 October 2026",
    paragraphs: [
      "POWER-AI-WEB records learning behavior while you use the platform: activity times and durations; actions and progress through Prepare, Organize, Work, Evaluate and Rethink; practice attempts, Practice/Evaluate results and mastery indicators. This behavioral data is used only for educational research and product improvement. It is not sold or used for advertising.",
      "Analysis may include historical records already stored by the system and does not depend on a Google Form response. Only authorized research administrators can export data. Behavioral CSV files use participant codes instead of names and email addresses and exclude conversation content and free-text answers. The email-to-participant mapping is managed separately and used only when data linkage is needed for these two purposes; identifiable student data is not published.",
      "For questions about your data or requests to review, correct or delete it, contact ttduy@sgu.edu.vn.",
    ],
    summary: "Learning behavior data, including stored history, is collected only for educational research and product improvement.",
    link: "Read the data terms",
  },
};

export function ResearchDataNotice({ language = "vi", compact = false }: {
  language?: "vi" | "en";
  compact?: boolean;
}) {
  const notice = notices[language];
  if (compact) {
    return <p className="auth-legal">{notice.summary} <Link href="/legal#learning-data">{notice.link}</Link>.</p>;
  }
  return (
    <section id="learning-data" className="card legal-card">
      <h2>{notice.title}</h2>
      <small className="muted">{notice.updated}</small>
      {notice.paragraphs.map(paragraph => <p key={paragraph}>{paragraph}</p>)}
    </section>
  );
}
