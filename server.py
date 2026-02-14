from mcp.server.fastmcp import FastMCP, Image
import json
import subprocess
import os
import tempfile
from PIL import Image as PILImage
import io
import numpy as np

temp_dir = tempfile.mkdtemp()

mcp = FastMCP("Typst MCP Server")

# load the typst docs JSON file
raw_typst_docs = ""
with open(os.path.join(os.path.dirname(__file__), "typst-docs", "main.json"), "r", encoding="utf-8") as f:
    raw_typst_docs = f.read()
typst_docs = json.loads(raw_typst_docs)

def list_child_routes(chapter: dict) -> list[dict]:
    """
    Lists all child routes of a chapter.
    """
    if "children" not in chapter:
        return []
    child_routes = [] # { "route": str, content_length: int }[]
    for child in chapter["children"]:
        if "route" in child:
            child_routes.append({
                "route": child["route"],
                "content_length": len(json.dumps(child))
            })
        child_routes += list_child_routes(child)
    return child_routes


@mcp.tool()
def list_docs_chapters() -> str:
    """
    Lists all chapters in the typst docs.
    The LLM should use this in the beginning to get the list of chapters and then decide which chapter to read.
    """
    print("mcp.resource('docs://chapters') called", file=sys.stderr)
    chapters = []
    for chapter in typst_docs:
        chapters.append({
            "route": chapter["route"],
            "content_length": len(json.dumps(chapter))
        })
        chapters += list_child_routes(chapter)
    return json.dumps(chapters)

@mcp.tool()
def get_docs_chapter(route: str) -> str:
    """
    Gets a chapter by route.
    The route is the path to the chapter in the typst docs.
    For example, the route "____reference____layout____colbreak" corresponds to the chapter "reference/layout/colbreak".
    The route is a string with underscores ("____") instead of slashes (because MCP uses slashes to separate the input parameters).
    
    If a chapter has children and its content length is over 1000, this will only return the child routes
    instead of the full content to avoid overwhelming responses.
    """
    print(f"mcp.resource('docs://chapters/{route}') called", file=sys.stderr)

    # the rout could also be in the form of "____reference____layout____colbreak" -> "/reference/layout/colbreak"
    # replace all underscores with slashes
    route = route.replace("____", "/")

    def route_matches(chapter_route: str, input_route: str) -> bool:
        return chapter_route.strip("/") == input_route.strip("/")

    def get_child(chapter: dict, route: str) -> dict:
        """
        Gets a child chapter by route.
        """
        if "children" not in chapter:
            return {}
        for child in chapter["children"]:
            if route_matches(child["route"], route):
                return child
            child = get_child(child, route)
            if child:
                return child
        return {}
    
    # Find the requested chapter
    found_chapter = None
    for chapter in typst_docs:
        if route_matches(chapter["route"], route):
            found_chapter = chapter
            break
        child = get_child(chapter, route)
        if child:
            found_chapter = child
            break
    
    if not found_chapter:
        return json.dumps({})
    
    # Check if chapter has children and is large
    content_length = len(json.dumps(found_chapter))
    if "children" in found_chapter and len(found_chapter["children"]) > 0 and content_length > 1000:
        # Return just the child routes instead of full content
        child_routes = []
        for child in found_chapter["children"]:
            if "route" in child:
                child_routes.append({
                    "route": child["route"],
                    "content_length": len(json.dumps(child))
                })
        
        # Create simplified chapter with only essential info and child routes
        simplified_chapter = {
            "route": found_chapter["route"],
            "title": found_chapter.get("title", ""),
            "content_length": content_length,
            "note": "This chapter is large. Only child routes are shown. Request specific child routes for detailed content.",
            "child_routes": child_routes
        }
        return json.dumps(simplified_chapter)
    
    return json.dumps(found_chapter)

@mcp.tool()
def get_docs_chapters(routes: list) -> str:
    """
    Gets multiple chapters by their routes.
    Takes a list of routes and returns a JSON stringified list of results.
    
    Example:
    Input: ["____reference____layout____colbreak", "____reference____text____text"]
    Output: JSON stringified list containing the content of both chapters
    """
    results = []
    for route in routes:
        results.append(json.loads(get_docs_chapter(route)))
    return json.dumps(results)

@mcp.tool()
def latex_snippet_to_typst(latex_snippet) -> str:
    r"""
    Converts a latex to typst using pandoc.

    LLMs are way better at writing latex than typst.
    So the LLM should write the wanted output in latex and use this tool to convert it to typst.
    
    If it was not valid latex, the tool returns "ERROR: in latex_to_typst. Failed to convert latex to typst. Error message from pandoc: {error_message}".

    This should be used primarily for converting small snippets of latex to typst but it can also be used for larger snippets.

    Example 1:
    ```latex
    "$ f\in K ( t^ { H } , \beta ) _ { \delta } $"
    ```
    gets converted to:
    ```typst
    $f in K \( t^H \, beta \)_delta$
    ```

    Example 2:
    ```latex
    \begin{figure}[t]
        \includegraphics[width=8cm]{"placeholder.png"}
        \caption{Placeholder image}
        \label{fig:placeholder}
        \centering
    \end{figure}
    ```
    gets converted to:
    ```typst
    #figure(image("placeholder.png", width: 8cm),
        caption: [
            Placeholder image
        ]
    )
    <fig:placeholder>
    ```
    """
    # create a main.tex file with the latex_snippet
    with open(os.path.join(temp_dir, "main.tex"), "w") as f:
        f.write(latex_snippet)

    # run the pandoc command line tool and capture error output
    try:
        result = subprocess.run(
            ["pandoc", os.path.join(temp_dir, "main.tex"), "--from=latex", "--to=typst", "--output", os.path.join(temp_dir, "main.typ")],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip() if e.stderr else "Unknown error"
        return f"ERROR: in latex_to_typst. Failed to convert latex to typst. Error message from pandoc: {error_message}"
    
    # read the typst file
    with open(os.path.join(temp_dir, "main.typ"), "r") as f:
        typst = f.read()
        typst = typst.strip()

    return typst

@mcp.tool()
def latex_snippets_to_typst(latex_snippets: list) -> str:
    r"""
    Converts multiple latex snippets to typst.
    Takes a list of LaTeX snippets and returns a JSON stringified list of results.
    
    Example:
    Input: ["$f\in K ( t^ { H } , \beta ) _ { \delta }$", "\\begin{align} a &= b \\\\ c &= d \\end{align}"]
    Output: JSON stringified list containing the converted typst for each snippet
    """
    results = []
    # Ensure latex_snippets is actually a list
    if not isinstance(latex_snippets, list):
        try:
            latex_snippets = json.loads(latex_snippets)
        except:
            pass
    
    for snippet in latex_snippets:
        results.append(latex_snippet_to_typst(snippet))
    return json.dumps(results)

@mcp.tool()
def check_if_snippet_is_valid_typst_syntax(typst_snippet) -> str:
    r"""
    Checks if the given typst text is valid typst syntax.
    Returns "VALID" if it is valid, otherwise returns "INVALID! Error message: {error_message}".
    
    The LLM should use this to check if the typst syntax it generated is valid.
    If not valid, the LLM should try to fix it and check again.
    This should be used primarily for checking small snippets of typst syntax but it can also be used for larger snippets.

    Example 1:
    ```typst
    "$f in K \( t^H \, beta \)_delta$"
    ```
    returns: VALID

    Example 2:
    ```typst
    $a = \frac{1}{2}$ // not valid typst syntax (\frac is a latex command and not a typst command)
    ```
    returns: INVALID! Error message: {error: unknown variable: rac
        ┌─ temp.typ:1:7
        │
        1 │ $a = \frac{1}{2}$
        │        ^^^
        │
        = hint: if you meant to display multiple letters as is, try adding spaces between each letter: `r a c`
        = hint: or if you meant to display this as text, try placing it in quotes: `"rac"`}
    
    """

    # create a main.typ file with the typst
    with open(os.path.join(temp_dir, "main.typ"), "w") as f:
        f.write(typst_snippet)
    # run the typst command line tool and capture the result
    try:
        subprocess.run(
            ["typst", "compile", os.path.join(temp_dir, "main.typ")],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return "VALID"
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip() if e.stderr else "Unknown error"
        return f"INVALID! Error message: {error_message}"

@mcp.tool()
def check_if_snippets_are_valid_typst_syntax(typst_snippets: list) -> str:
    r"""
    Checks if multiple typst snippets have valid syntax.
    Takes a list of typst snippets and returns a JSON stringified list of results.

    The LLM should use this for example to check every single typst snippet it generated.
    
    Example:
    Input: ["$f in K \( t^H \, beta \)_delta$", "#let x = 1\n#x"]
    Output: JSON stringified list containing validation results ("VALID" or error messages)
    """
    results = []
    # Ensure typst_snippets is actually a list
    if not isinstance(typst_snippets, list):
        try:
            typst_snippets = json.loads(typst_snippets)
        except:
            pass
    
    for snippet in typst_snippets:
        results.append(check_if_snippet_is_valid_typst_syntax(snippet))
    return json.dumps(results)

@mcp.tool()
def typst_snippet_to_image(typst_snippet) -> Image | str:
    r"""
    Converts a typst text to an image using the typst command line tool.
    It is capable of converting multiple pages to a single png image.
    The image gets cropped to the content and padded with 10px on each side.

    The LLM should use this to convert typst to an image and then evaluate if the image is what it wanted.
    If not valid, the LLM should try to fix it and check again.
    This should be used primarily for converting small snippets of typst to images but it can also be used for larger snippets.

    Example 1:
    ```typst
    "$f in K \( t^H \, beta \)_delta$"
    ```
    gets converted to:
    ```image
    <image object>
    ```

    Example 2:
    ```typst
    #figure(image("placeholder.png", width: 8cm),
        caption: [
            Placeholder image
        ]
    )
    <fig:placeholder>
    ```
    gets converted to:
    ```image
    <image object>
    ```

    """
    
    # create a main.typ file with the typst
    with open(os.path.join(temp_dir, "main.typ"), "w") as f:
        f.write(typst_snippet)
    
    # run the typst command line tool and capture the result
    try:
        subprocess.run(
            ["typst", "compile", os.path.join(temp_dir, "main.typ"), "--format", "png", "--ppi", "500", os.path.join(temp_dir, "page{0p}.png")],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        
        # Find all generated pages
        page_files = []
        page_num = 1
        while os.path.exists(os.path.join(temp_dir, f"page{page_num}.png")):
            page_files.append(os.path.join(temp_dir, f"page{page_num}.png"))
            page_num += 1
        
        if not page_files:
            return "ERROR: in typst_to_image. No pages were generated."
        
        # Load all pages using PIL and crop to content
        pages = []
        for page_file in page_files:
            img = PILImage.open(page_file)
            
            # Convert to numpy array for easier processing
            img_array = np.array(img)
            
            # Check if the image is RGB
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                # Find non-white pixels (R,G,B not all 255)
                non_white = np.where(~np.all(img_array == 255, axis=2))
            else:
                # For grayscale images
                non_white = np.where(img_array < 255)
            
            if len(non_white[0]) > 0:  # If there are non-white pixels
                # Find bounding box
                top = non_white[0].min()
                bottom = non_white[0].max()
                left = non_white[1].min()
                right = non_white[1].max()
                
                # Add some padding (10px on each side)
                padding = 10
                top = max(0, top - padding)
                bottom = min(img.height - 1, bottom + padding)
                left = max(0, left - padding)
                right = min(img.width - 1, right + padding)
                
                # Crop image to bounding box
                cropped_img = img.crop((left, top, right + 1, bottom + 1))
                pages.append(cropped_img)
            else:
                # If image is completely white, keep it as is
                pages.append(img)
        
        if not pages:
            return "ERROR: in typst_to_image. Failed to process page images."
        
        # Calculate total height
        total_width = max(page.width for page in pages)
        total_height = sum(page.height for page in pages)
        
        # Create a new image with the combined dimensions
        combined_image = PILImage.new('RGB', (total_width, total_height), (255, 255, 255))
        
        # Paste all pages vertically
        y_offset = 0
        for page in pages:
            # Center horizontally if page is narrower than the combined image
            x_offset = (total_width - page.width) // 2
            combined_image.paste(page, (x_offset, y_offset))
            y_offset += page.height
            
        # Save combined image to bytes
        img_bytes_io = io.BytesIO()
        combined_image.save(img_bytes_io, format="PNG")
        img_bytes = img_bytes_io.getvalue()
        
        # Clean up temp files
        os.remove(os.path.join(temp_dir, "main.typ"))
        for page_file in page_files:
            os.remove(page_file)
            
        return Image(data=img_bytes, format="png")
    
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip() if e.stderr else "Unknown error"
        return f"ERROR: in typst_to_image. Failed to convert typst to image. Error message from typst: {error_message}"

if __name__ == "__main__":

    mcp.run()
