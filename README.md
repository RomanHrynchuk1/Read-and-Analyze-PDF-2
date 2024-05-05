# Read and Analyze CV/Resume(PDF) files in python (including flat/image format)

#### The Challenge of Complex PDFs

Complex PDF files can be notoriously difficult to read and analyze due to their varied structures. This challenge is further amplified when dealing with non-editable PDFs (flat/image format). Traditionally, processing such files required advanced technical skills.

#### Enter GPT-4-Turbo

The introduction of the GPT-4-Turbo model with its powerful vision capabilities has revolutionized the game. It now allows even non-senior developers to extract valuable insights from complex, non-editable PDFs.

#### Guiding You Through the Process

This project aims to equip you with the knowledge and tools to leverage GPT-4-Turbo for effective PDF analysis.

## 1. Project Overview: CV/Resume Information Extraction

This project focuses on extracting key information from CVs and resumes in PDF format. The target data includes:

1. Name
2. Phone Number
3. Email Address
4. Address (Full Address including City, State, and Country)
5. Skills (e.g., Programming Languages like C++ and Java, Languages like English and French)
6. Education (Institute Name, Year, and Marks)
7. Work Experience (Start Date, End Date, Employer Name, and Role/Designation)
8. Certifications (e.g., CISCO, Microsoft, AWS, Oracle)

#### Challenges:

- **Unpredictable PDF Structure:** Resumes and CVs come from diverse sources, leading to inconsistent PDF layouts and structures.
- **Non-Editable PDFs:** Some PDFs are image-based or scanned documents, making it impossible to directly extract text using traditional methods.

#### Improvements:

- **Project Title:** Added a clear and concise title.
- **Terminology:** Used "CVs and resumes" instead of just "CV or resume" for broader scope.
- **Example Skills:** Provided examples of skills to make the list clearer.
- **Work Experience:** Rephrased the section for improved readability.
- **Challenges:** Expanded on the challenges for better understanding.

## 2. Extracting text from PDF file using pypdf

To install pypdf, run the following command from the command line:

`pip install pypdf`

```
# importing required classes
from pypdf import PdfReader

# creating a pdf reader object
reader = PdfReader('example.pdf')

# printing number of pages in pdf file
print(len(reader.pages))

# creating a page object
page = reader.pages[0]

# extracting text from page
print(page.extract_text())
```

**Let us try to understand the above code in chunks:**
`reader = PdfReader('example.pdf')`
Here, we create an object of PdfReader class of pypdf module and pass the path to the PDF file & get a PDF reader object.

`print(len(reader.pages))`
pages property gives the number of pages in the PDF file. For example, in our case, it is 20 (see first line of output).

`pageObj = reader.pages[0]`
Now, we create an object of PageObject class of pypdf module. PDF reader object has function pages[] which takes page number (starting from index 0) as argument and returns the page object.

`print(pageObj.extract_text())`
Page object has function extract_text() to extract text from the PDF page.

**Note:** While PDF files are great for laying out text in a way that’s easy for people to print and read, they’re not straightforward for software to parse into plaintext. As such, pypdf might make mistakes when extracting text from a PDF and may even be unable to open some PDFs at all. It isn’t much you can do about this, unfortunately. pypdf may simply be unable to work with some of your particular PDF files.

## 2. How to read the PDF files in flat/image format using the OpenAI vision model

The current best OpenAI vision model is "GPG-4-Turbo"

**- Create a openai Client:**

```
model_name = "gpt-4-turbo"

client = OpenAI(
    api_key=api_key,
    # max_retries=3,
    timeout=600.0, # The real analysis time is much smaller than this.
)
```

**- Convert PDF to image:**

```
def pdf_to_image(pdf_local, workdir):
    try:
        pdf_images = convert_from_path(pdf_path=pdf_local, poppler_path=None)  # "./bin"
    except:  # noqa: E722
        msg = """You need to install Poppler on your system to convert PDF to Image.
            - On Mac System, run the following command in Terminal:
                brew install poppler

            - On Windows System, do the following:
                1. Download the latest poppler package from [https://github.com/oschwartz10612/poppler-windows/releases/] version which is the most up-to-date.
                2. Move the extracted directory to the desired place on your system
                3. Add the 'bin/' directory to your PATH
                4. Test that all went well by opening cmd and making sure that you can call 'pdftoppm -h'

            Please visit [https://pdf2image.readthedocs.io/en/latest/installation.html] for more detailed information.
            """
        print(msg)
        return False
    for idx in range(len(pdf_images)):
        pdf_images[idx].save(f"{workdir}/{idx+1}.png", "PNG")
    return True
```

**- Encode image to parameter and send to OpenAI to extract text from them:**

```
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def image_to_text(image_local):
    image_url = f"data:image/png;base64,{encode_image(image_local)}"

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": [
                    # {"type": "text", "text": "This image contains a flat/image PDF transcript. Please extract all the text from the image."},
                    {
                        "type": "text",
                        "text": "Extract all the text from this image of a flat/image PDF transcript. Provide the extracted text only, without any descriptions.",
                    },
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
    )

    result = response.choices[0].message.content
    return result
```

**This is a skill that anyone can learn with dedication! Best regards.**
