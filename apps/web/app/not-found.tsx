import Link from "next/link";

export default function NotFound() {
  return (
    <div className="center-page">
      <div className="status-panel">
        <strong>Không tìm thấy nội dung</strong>
        <p>Bài học hoặc trang bạn yêu cầu không tồn tại trong catalog POWER hiện tại.</p>
        <Link className="button primary inline" href="/learn">Về danh mục bài học</Link>
      </div>
    </div>
  );
}
