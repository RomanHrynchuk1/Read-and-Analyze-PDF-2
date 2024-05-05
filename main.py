import os
import re
import json
import base64
import unicodedata
from pypdf import PdfReader
from pdf2image import convert_from_path
from openai import OpenAI

from config import api_key

"""
- In Windows System: 
    pip install json
    pip install base64
    pip install unicodedata
    pip install pypdf
    pip install pdf2image
    pip install openai
    
- In Mac System:
    python3 -m pip install json
    python3 -m pip install base64
    python3 -m pip install unicodedata2
    python3 -m pip install pypdf
    python3 -m pip install pdf2image
    python3 -m pip install openai
"""

INPUT_DIR = "./INPUT/"
OUTPUT_DIR = "./OUTPUT/"

model_name = "gpt-4-turbo"

client = OpenAI(
    api_key=api_key,
    # max_retries=3,
    timeout=600.0,
)


def unicodeToAscii(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def normalize_text(text):
    # Replace sequential spaces with a single space
    # return text
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Replace three or more new-line characters with two new-line characters
    normalized_text = re.sub(r"\n{3,}", "\n\n", text)

    return normalized_text


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


def flat_pdf_to_text(pdf_local):
    """
    Extract text from Flat/Image Transcripts.
    """

    workdir = "./workdir/images"
    if os.path.exists(workdir):
        # Get all files in the directory
        files = os.listdir(workdir)

        for filename in files:
            # Construct the full path
            file_path = os.path.join(workdir, filename)
            # Check if it's a file (not a subdirectory)
            if os.path.isfile(file_path):
                os.remove(file_path)

        print(f"*.png files already exists in [{workdir}]. removing done.")

    os.makedirs(workdir, exist_ok=True)

    if not pdf_to_image(pdf_local=pdf_local, workdir=workdir):
        return False

    print(f"Convert {pdf_local} to images and saving at [{workdir}] done.")

    image_files = []
    for filename in os.listdir(workdir):
        if filename.endswith(".png"):
            image_files.append(filename)

    cnt = len(image_files)
    result_text = ""
    for i in range(cnt):
        print(f"Start page {i+1} of {cnt}.", end="\n")
        result = image_to_text(f"{workdir}/{i+1}.png") + "\n"
        print(f"Finished page {i+1} of {cnt} with the following result:\n{result}")
        result_text += result

    return result_text


def get_content(file_path):
    """
    This function attempts to extract text content from a PDF file using PyPDF (if available).

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        str: The extracted text content from the PDF file (if successful).

    Raises:
        ValueError: If the provided file path does not exist or is not a PDF file.
        ImportError: If the PyPDF library is not found.
    """

    # Check if file exists and has .pdf extension
    if not os.path.exists(file_path) or not file_path.lower().endswith(".pdf"):
        raise ValueError(f"Invalid file path '{file_path}'")

    try:
        # creating a pdf reader object
        reader = PdfReader(file_path)
    except ImportError:
        raise ImportError(
            "pypdf library not found. Please install it using 'pip install pypdf' (if available)."
        )
    except FileNotFoundError:
        raise ValueError(f"PDF file not found at '{file_path}'")

    # Extract text from all pages (might not be reliable)
    text_content = ""
    for page in reader.pages:
        # Text extraction using getPage().extractText() (limited capabilities)
        text_content += page.extract_text() + "\n"

    ret = normalize_text(text_content)

    # If this is a flat/image format.
    if len(re.sub(r"[\s\n]+", "", ret)) > 1000:
        print("Getting file content: done.")
    else:
        print("Detected as a Flat/Image PDF.")
        ret = flat_pdf_to_text(file_path)
        if not ret:
            return False
        print("Getting file content: done.")

    return ret


#####################################################################################################################

to_openai_pre = """Let me know the following information in JSON format from the given CV/Resume Name & Content:

File Name & Content (I extracted the Content from a PDF file using pypdf in Python):
###
PDF Name:
"{pdf_name}"
PDF Content:
{pdf_content}
###
"""

to_openai_suf = """
What I want to know are:
1. Name
2. Phone
3. Email
4. Address ( Address, city, state, country)
5. Gender
6. Date of birth
7. Skills ( Ex, C++, Java, English language, French language, etc )
8. Education ( Institute name, Year, Marks)
9. Previous Employers ( Date from, date to, Employer name, Role / Designation )
10. Certificates ( CISCO, Microsoft, AWS, Oracle etc )

JSON structure:
{
    "Name": "",
    "Phone": "",
    "Email": "",
    "Address": {
        "Address": "",
        "City": "",
        "State": "",
        "Country": ""
    },
    "Gender": "",
    "Date of Birth": "",
    "Skills": [
        "",
        ...
    ],
    "Education": [
        {
            "Institute Name": "",
            "Year": "",
            "Marks": ""
        },
        ...
    ],
    "Previous Employers": [
        {
            "Date from": "",
            "Date to": "",
            "Employer Name": "",
            "Role/Designation": ""
        },
        ...
    ],
    "Certificates": [
        "",
        ...
    ]
}

When some values are missing, put "N/A" in those fields.
"""


def chat(text, get_json_result=True):
    f, ret = True, ""
    try:
        while not ret:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
            )
            ret = response.choices[0].message.content
            if get_json_result:
                try:
                    ret = json.loads(ret)
                except Exception as ex:
                    print(ex)
                    ret = False
    except Exception as ex:
        print(str(ex))
        f = False
    finally:
        return f, ret


def get_result(file_name, file_content):
    global to_openai_pre, to_openai_suf
    text = (
        to_openai_pre.format(pdf_name=file_name, pdf_content=file_content)
        + to_openai_suf
    )
    # with open("./error.txt", "w", encoding="utf-8") as err:
    #     err.write(text)
    # exit(0)

    f, ret = chat(text)
    if f:
        return ret
    else:
        print("Failed!")
        return dict()


#####################################################################################################################


def check_gender(gender_string, name_string):
    if gender_string in ["Male", "Female"] or name_string in ["", "N/A"]:
        return gender_string
    msg = f"The name is {name_string}. What is the gender? The answer should be one of ['Male', 'Female', 'Not Sure']\n\
        The answer should be JSON format: {{\"Gender\": ?}}"
    f, ret = chat(msg)

    if f and "Gender" in ret:
        return ret["Gender"]

    return gender_string


def check_email(email_string):
    pat = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    if re.match(pat, email_string):
        return email_string
    else:
        if not email_string or email_string == "N/A":
            return "N/A"
        else:
            msg = f'The email address is {email_string}. Check if this is the right format and provide me with the correct one.\n\
                The answer should be JSON format: {{"Email": ?}}'
            f, ret = chat(msg)

            if f and "Email" in ret:
                return ret["Email"]

            return email_string


if __name__ == "__main__":
    try:
        if not os.path.exists(INPUT_DIR):
            print(
                "Input directory not exists! Please check out the name and then try again! : 'INPUT'"
            )
            exit(0)

        print("Started!")

        # Check if the output directory already exists
        if not os.path.exists(OUTPUT_DIR):
            # If it doesn't exist, create the directory
            os.makedirs(OUTPUT_DIR)

        # Get a list of all files in the directory
        files = os.listdir(INPUT_DIR)
        input_files = []

        # Loop through each file in the directory
        for file_name in files:
            # Check if the file is a regular file (not a directory)
            real_name = os.path.join(INPUT_DIR, file_name)
            if os.path.isfile(real_name) and real_name.lower().endswith(".pdf"):
                input_files.append(real_name)

        print(f"{len(input_files) } total file(s) found in the 'INPUT' directory.")

        # Loop files one by one.
        for file_name in input_files:
            real_name = file_name[file_name.rfind("/") + 1 :]
            print(f"=+=+=+=+=  {real_name}  =+=+=+=+=")
            file_content = get_content(file_name)
            if not file_content:
                print("Error: Can't read the content of the PDF file.")
                continue
            # with open(
            #     f"{OUTPUT_DIR}{real_name}.txt",
            #     "w",
            #     encoding="utf-8",
            # ) as f:
            #     f.write(file_content)

            result = get_result(real_name, file_content)
            if "Gender" in result.keys():
                result["Gender"] = check_gender(result["Gender"], result["Name"])

            if "Email" in result.keys():
                result["Email"] = check_email(result["Email"])

            print("Getting result: done.")

            save_name = f"{OUTPUT_DIR}{real_name}.json"
            result_string = json.dumps(
                result, sort_keys=False, indent=4, ensure_ascii=False
            )

            with open(save_name, "w", encoding="utf-8") as f:
                f.write(result_string)
                print("Result saved!")
            print("")
            break

    except Exception as ex:
        print(f"An error occurred: {ex}")
