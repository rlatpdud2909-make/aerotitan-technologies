from io import BytesIO
from pypdf import PdfReader

MAX_BYTES=5*1024*1024
MAX_PAGES=10

def extract_pdf(data: bytes):
    if not data or len(data)>MAX_BYTES or not data.startswith(b'%PDF-'):
        raise ValueError('유효한 PDF가 아니거나 5MB 크기 제한을 초과했습니다.')
    try:
        reader=PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted: raise ValueError('암호화된 PDF는 지원하지 않습니다.')
        if not 1 <= len(reader.pages) <= MAX_PAGES: raise ValueError('PDF는 1~10페이지만 지원합니다.')
        pages=[page.extract_text() or '' for page in reader.pages]
    except ValueError: raise
    except Exception as exc: raise ValueError('PDF를 읽을 수 없습니다.') from exc
    if any(not p.strip() for p in pages): raise ValueError('빈 페이지 또는 텍스트 추출에 실패한 페이지가 있습니다. OCR은 지원하지 않습니다.')
    if sum(map(len,pages))>100000: raise ValueError('문서 텍스트가 너무 깁니다.')
    return pages
