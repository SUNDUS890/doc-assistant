from pypdf import PdfReader

reader = PdfReader("data/sample.pdf")
print("Number of pages:", len(reader.pages))
print("---- First 500 characters of page 1 ----")
print(reader.pages[0].extract_text()[:500])