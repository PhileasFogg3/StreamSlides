import tkinter as tk
from tkinter import messagebox, simpledialog, colorchooser
import json
import os
import time
import shutil
import sys
from pathlib import Path

# --- Directory Setup ---
DOCUMENTS_DIR = Path.home() / "Documents" / "StreamSlides"
DECKS_DIR = DOCUMENTS_DIR / "Decks"
DECKS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_WORDS = Path(getattr(sys, '_MEIPASS', '.')) / "resources" / "words.json"
slide_file = DECKS_DIR / "default.json"
output_file = DOCUMENTS_DIR / "slide_data.json"
html_output = DOCUMENTS_DIR / "slide_output.html"
backup_dir = DOCUMENTS_DIR / "backups"
backup_dir.mkdir(exist_ok=True)

if not slide_file.exists():
    shutil.copyfile(DEFAULT_WORDS, slide_file)

slides = []
current = 0
last_edit_time = time.time()
font_size = 28  # Default font size (will be overwritten by loaded value)

# --- Slide Management ---
def load_slides(path=None):
    global slides, font_size
    path = path or slide_file
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "slides" in data and "font_size" in data:
                slides[:] = data["slides"]
                font_size = data.get("font_size", 28)
            else:
                slides[:] = data
                font_size = 28
    else:
        slides[:] = [{"text": "", "bold": False, "underline": False, "italic": False, "color": "#FFFFFF"}]
        font_size = 28

def save_slides():
    data = {
        "slides": slides,
        "font_size": font_size
    }
    with open(slide_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    shutil.copyfile(slide_file, backup_dir / f"{slide_file.stem}_backup_{timestamp}.json")
    autosave_label.config(text="Autosaved ✔", fg="green")
    root.after(2000, lambda: autosave_label.config(text=""))
    update_window_title()

def write_current_slide():
    data_to_write = slides[current].copy()
    data_to_write["font_size"] = font_size
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data_to_write, f)
    write_slide_html()

def write_slide_html():
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Slide Text</title>
<style>
  body {{
    margin: 0;
    background: transparent;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.3;
    text-align: center;
    white-space: pre-wrap;
    color: white;
  }}
  #slideText {{ white-space: pre-wrap; }}
  .bold {{ font-weight: bold; }}
  .underline {{ text-decoration: underline; }}
  .italic {{ font-style: italic; }}
</style>
</head>
<body>
  <div id="slideText"></div>
<script>
  const slideTextDiv = document.getElementById("slideText");
  let lastText = "", lastBold = false, lastUnderline = false, lastItalic = false, lastColor = "", lastFontSize = 0;

  async function fetchSlideData() {{
    try {{
      const url = 'slide_data.json?_=' + new Date().getTime();
      const response = await fetch(url, {{cache: "no-store"}});
      if (!response.ok) throw new Error("Network response not OK");
      const data = await response.json();

      if (data.font_size !== lastFontSize) {{
        lastFontSize = data.font_size || 28;
        document.body.style.fontSize = lastFontSize + "px";
      }}

      if (
        data.text !== lastText ||
        data.bold !== lastBold ||
        data.underline !== lastUnderline ||
        data.italic !== lastItalic ||
        data.color !== lastColor
      ) {{
        lastText = data.text;
        lastBold = data.bold;
        lastUnderline = data.underline;
        lastItalic = data.italic;
        lastColor = data.color || "white";

        slideTextDiv.textContent = lastText;
        slideTextDiv.className = "";
        if (lastBold) slideTextDiv.classList.add("bold");
        if (lastUnderline) slideTextDiv.classList.add("underline");
        if (lastItalic) slideTextDiv.classList.add("italic");
        slideTextDiv.style.color = lastColor;
      }}
    }} catch (err) {{
      console.error("Error fetching slide data:", err);
    }}
  }}

  setInterval(fetchSlideData, 1000);
  fetchSlideData();
</script>
</body>
</html>"""
    with open(html_output, "w", encoding="utf-8") as f:
        f.write(html_content)

# --- UI Functions ---
def show_slide():
    text.delete("1.0", tk.END)
    text.insert(tk.END, slides[current]["text"])
    bold_var.set(slides[current].get("bold", False))
    underline_var.set(slides[current].get("underline", False))
    italic_var.set(slides[current].get("italic", False))
    slide_listbox.selection_clear(0, tk.END)
    slide_listbox.selection_set(current)
    slide_listbox.see(current)
    color = slides[current].get("color", "#FFFFFF")
    color_btn.config(bg=color)
    color_btn.config(fg="white" if color.lower() == "#000000" else "black")
    write_current_slide()

def next_slide():
    global current
    if current < len(slides) - 1:
        current += 1
        show_slide()

def prev_slide():
    global current
    if current > 0:
        current -= 1
        show_slide()

def add_slide():
    slides.insert(current + 1, {"text": "", "bold": False, "underline": False, "italic": False, "color": "#FFFFFF"})
    refresh_slide_list()
    next_slide()
    save_slides()

def remove_slide():
    global current
    if len(slides) > 1:
        del slides[current]
        current = max(0, current - 1)
        refresh_slide_list()
        show_slide()
        save_slides()

def move_slide(offset):
    global current
    new_index = current + offset
    if 0 <= new_index < len(slides):
        slides[current], slides[new_index] = slides[new_index], slides[current]
        current = new_index
        refresh_slide_list()
        show_slide()
        save_slides()

def update_slide():
    slides[current]["text"] = text.get("1.0", tk.END).strip()
    slides[current]["bold"] = bold_var.get()
    slides[current]["underline"] = underline_var.get()
    slides[current]["italic"] = italic_var.get()
    slide_listbox.delete(current)
    slide_listbox.insert(current, get_slide_title(slides[current]))
    write_current_slide()
    save_slides()

def choose_color():
    color_code = colorchooser.askcolor(title="Choose text color")[1]
    if color_code:
        slides[current]["color"] = color_code
        color_btn.config(bg=color_code)
        color_btn.config(fg="white" if color_code.lower() == "#000000" else "black")
        update_slide()

def on_slide_select(event):
    global current
    selection = slide_listbox.curselection()
    if selection:
        current = selection[0]
        show_slide()

def refresh_slide_list():
    slide_listbox.delete(0, tk.END)
    for slide in slides:
        slide_listbox.insert(tk.END, get_slide_title(slide))

def get_slide_title(slide):
    return slide['text'].strip().split('\n')[0][:30] + ("..." if len(slide['text']) > 30 else "")

def mark_text_edited(event=None):
    global last_edit_time
    last_edit_time = time.time()
    root.after(1000, try_autosave)

def try_autosave():
    if time.time() - last_edit_time >= 1:
        update_slide()

def update_window_title():
    root.title(f"StreamSlides - {slide_file.name}")

def refresh_file_list():
    file_listbox.delete(0, tk.END)
    for f in sorted(DECKS_DIR.glob("*.json")):
        file_listbox.insert(tk.END, f.name)

def load_selected_file():
    global slide_file, current
    selection = file_listbox.curselection()
    if selection:
        selected = file_listbox.get(selection[0])
        slide_file = DECKS_DIR / selected
        load_slides(slide_file)
        current = 0
        refresh_slide_list()
        show_slide()
        update_window_title()

def save_as():
    global slide_file
    name = simpledialog.askstring("Save As", "Enter a name for the slide deck (no extension):")
    if name:
        if not name.endswith(".json"):
            name += ".json"
        new_path = DECKS_DIR / name
        slide_file = new_path
        save_slides()
        refresh_file_list()
        messagebox.showinfo("Saved", f"Saved as {name}")

def new_file():
    global slides, current, slide_file, font_size
    name = simpledialog.askstring("New Deck", "Enter a name for the new slide deck (no extension):")
    if name:
        if not name.endswith(".json"):
            name += ".json"
        slide_file = DECKS_DIR / name
        slides = [{"text": "", "bold": False, "underline": False, "italic": False, "color": "#FFFFFF"}]
        current = 0
        font_size = 28
        refresh_slide_list()
        show_slide()
        save_slides()
        refresh_file_list()

def update_font_size(event=None):
    global font_size
    try:
        size = int(font_size_entry.get())
        if 8 <= size <= 100:
            font_size = size
            write_slide_html()
            save_slides()
            autosave_label.config(text=f"Font size set to {font_size}px", fg="blue")
        else:
            raise ValueError
    except ValueError:
        messagebox.showerror("Invalid", "Enter a number between 8 and 100.")

# --- Drag and Drop for slides ---
drag_data = {"start_index": None}
def handle_drop(event):
    end_index = slide_listbox.nearest(event.y)
    start_index = drag_data["start_index"]
    if start_index != end_index and 0 <= start_index < len(slides) and 0 <= end_index < len(slides):
        slides.insert(end_index, slides.pop(start_index))
        global current
        current = end_index
        refresh_slide_list()
        show_slide()
        save_slides()

# --- GUI Setup ---
root = tk.Tk()
frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

tk.Label(frame, text="List of Available Decks").grid(row=0, column=0)
file_listbox = tk.Listbox(frame, height=10, width=25)
file_listbox.grid(row=1, column=0, rowspan=6, padx=(0,10))
tk.Button(frame, text="Load File", command=load_selected_file).grid(row=7, column=0, sticky="ew")
tk.Button(frame, text="New File", command=new_file).grid(row=8, column=0, sticky="ew")
tk.Button(frame, text="Save As...", command=save_as).grid(row=9, column=0, sticky="ew")

tk.Label(frame, text="List of Slides in this Deck").grid(row=0, column=1)
slide_listbox = tk.Listbox(frame, height=10, width=30)
slide_listbox.grid(row=1, column=1, rowspan=6)
slide_listbox.bind('<<ListboxSelect>>', on_slide_select)
slide_listbox.bind("<Button-1>", lambda e: drag_data.update(start_index=slide_listbox.nearest(e.y)))
slide_listbox.bind("<ButtonRelease-1>", lambda e: handle_drop(e))

text = tk.Text(frame, wrap=tk.WORD, height=10, width=50)
text.grid(row=1, column=2, columnspan=6)
text.bind("<KeyRelease>", mark_text_edited)

bold_var = tk.BooleanVar()
underline_var = tk.BooleanVar()
italic_var = tk.BooleanVar()
tk.Checkbutton(frame, text="Bold", variable=bold_var, command=update_slide).grid(row=2, column=2, sticky="w")
tk.Checkbutton(frame, text="Underline", variable=underline_var, command=update_slide).grid(row=2, column=3, sticky="w")
tk.Checkbutton(frame, text="Italic", variable=italic_var, command=update_slide).grid(row=2, column=4, sticky="w")

color_btn = tk.Button(frame, text="Text Color", command=choose_color)
color_btn.grid(row=2, column=5, sticky="w")

tk.Button(frame, text="Prev Slide", command=prev_slide).grid(row=3, column=2)
tk.Button(frame, text="Next Slide", command=next_slide).grid(row=3, column=3)
tk.Button(frame, text="Add Slide", command=add_slide).grid(row=3, column=4)
tk.Button(frame, text="Remove Slide", command=remove_slide).grid(row=3, column=5)

tk.Button(frame, text="Move Slide Up", command=lambda: move_slide(-1)).grid(row=4, column=2)
tk.Button(frame, text="Move Slide Down", command=lambda: move_slide(1)).grid(row=4, column=3)

tk.Label(frame, text="Font Size:").grid(row=5, column=2, sticky="e")
font_size_entry = tk.Entry(frame, width=5)
font_size_entry.grid(row=5, column=3, sticky="w")
font_size_entry.bind("<Return>", update_font_size)

autosave_label = tk.Label(frame, text="", fg="green")
autosave_label.grid(row=6, column=2, columnspan=3)

# --- Initialization ---
refresh_file_list()
load_slides(slide_file)
font_size_entry.delete(0, tk.END)
font_size_entry.insert(0, str(font_size))
refresh_slide_list()
show_slide()
update_window_title()

root.mainloop()