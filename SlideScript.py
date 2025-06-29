import tkinter as tk
from tkinter import messagebox, simpledialog, colorchooser
import json
import os
import time
import shutil
import sys

def resource_path(relative_path):
    """ Get absolute path to resource inside PyInstaller bundle or dev folder. """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

BASE_DIR = os.path.abspath(".")
DEFAULT_WORDS = resource_path("resources/words.json")
slide_file = os.path.join(BASE_DIR, "words.json")
slide_data_file = os.path.join(BASE_DIR, "slide_data.json")  # JSON output for current slide
html_output = os.path.join(BASE_DIR, "slide_output.html")
backup_dir = os.path.join(BASE_DIR, "backups")

# Create backup folder if not present
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

# Copy default words.json if none exists
if not os.path.exists(slide_file):
    shutil.copyfile(DEFAULT_WORDS, slide_file)

slides = []
current = 0
last_edit_time = time.time()

def load_slides():
    global slides
    if os.path.exists(slide_file):
        with open(slide_file, "r", encoding="utf-8") as f:
            slides = json.load(f)
    else:
        slides = [{"text": "", "bold": False, "underline": False, "color": "#FFFFFF"}]

def save_slides():
    with open(slide_file, "w", encoding="utf-8") as f:
        json.dump(slides, f, indent=2)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    shutil.copyfile(slide_file, os.path.join(backup_dir, f"words_backup_{timestamp}.json"))
    autosave_label.config(text="Autosaved ✔", fg="green")
    root.after(2000, lambda: autosave_label.config(text=""))

def write_current_slide():
    # Write the current slide info as JSON for Streamlabs
    current_slide = slides[current]
    slide_data = {
        "text": current_slide.get("text", ""),
        "bold": current_slide.get("bold", False),
        "underline": current_slide.get("underline", False),
        "color": current_slide.get("color", "#FFFFFF")
    }
    with open(slide_data_file, "w", encoding="utf-8") as f:
        json.dump(slide_data, f, indent=2)
    write_slide_html()

def write_slide_html():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Slide Text</title>
<style>
  body {
    margin: 0;
    background: transparent;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 28px;
    line-height: 1.3;
    text-align: center;
    white-space: pre-wrap;
    color: white;
  }
  #slideText {
    white-space: pre-wrap;
  }
  .bold { font-weight: bold; }
  .underline { text-decoration: underline; }
</style>
</head>
<body>
  <div id="slideText"></div>

<script>
  const slideTextDiv = document.getElementById("slideText");
  let lastText = "";
  let lastBold = false;
  let lastUnderline = false;
  let lastColor = "";

  async function fetchSlideData() {
    try {
      const url = 'slide_data.json?_=' + new Date().getTime();  // cache buster
      const response = await fetch(url, {cache: "no-store"});
      if (!response.ok) throw new Error("Network response not OK");
      const data = await response.json();

      if (
        data.text !== lastText ||
        data.bold !== lastBold ||
        data.underline !== lastUnderline ||
        data.color !== lastColor
      ) {
        lastText = data.text;
        lastBold = data.bold;
        lastUnderline = data.underline;
        lastColor = data.color || "white";

        slideTextDiv.textContent = lastText;
        slideTextDiv.className = "";
        if (lastBold) slideTextDiv.classList.add("bold");
        if (lastUnderline) slideTextDiv.classList.add("underline");
        slideTextDiv.style.color = lastColor;
      }
    } catch (err) {
      // Fail silently
      console.error("Error fetching slide data:", err);
    }
  }

  setInterval(fetchSlideData, 1000);
  fetchSlideData();
</script>
</body>
</html>
"""

    with open(html_output, "w", encoding="utf-8") as f:
        f.write(html_content)

def show_slide():
    text.delete("1.0", tk.END)
    text.insert(tk.END, slides[current]["text"])
    bold_var.set(slides[current].get("bold", False))
    underline_var.set(slides[current].get("underline", False))
    slide_listbox.selection_clear(0, tk.END)
    slide_listbox.selection_set(current)
    slide_listbox.see(current)
    color_btn.config(bg=slides[current].get("color", "#FFFFFF"))
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
    slides.insert(current + 1, {"text": "", "bold": False, "underline": False, "color": "#FFFFFF"})
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
    slide_listbox.delete(current)
    slide_listbox.insert(current, get_slide_title(slides[current]))
    write_current_slide()
    save_slides()

def choose_color():
    color_code = colorchooser.askcolor(title="Choose text color")[1]
    if color_code:
        slides[current]["color"] = color_code
        color_btn.config(bg=color_code)
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
    title = slide['text'].strip().split('\n')[0]
    return title[:30] + ("..." if len(title) > 30 else "")

def mark_text_edited(event=None):
    global last_edit_time
    last_edit_time = time.time()
    root.after(1000, try_autosave)

def try_autosave():
    if time.time() - last_edit_time >= 1:
        update_slide()

# GUI Setup
root = tk.Tk()
root.title("StreamSlides")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

slide_listbox = tk.Listbox(frame, height=10, width=30)
slide_listbox.grid(row=0, column=0, rowspan=6, padx=(0,10))
slide_listbox.bind('<<ListboxSelect>>', on_slide_select)

# Drag & Drop Logic
drag_data = {"start_index": None}
def on_drag_start(event):
    drag_data["start_index"] = slide_listbox.nearest(event.y)
def on_drag_drop(event):
    end_index = slide_listbox.nearest(event.y)
    start_index = drag_data["start_index"]
    if start_index != end_index and 0 <= start_index < len(slides) and 0 <= end_index < len(slides):
        slides.insert(end_index, slides.pop(start_index))
        global current
        current = end_index
        refresh_slide_list()
        show_slide()
        save_slides()
slide_listbox.bind("<Button-1>", on_drag_start)
slide_listbox.bind("<ButtonRelease-1>", on_drag_drop)

text = tk.Text(frame, wrap=tk.WORD, height=10, width=50)
text.grid(row=0, column=1, columnspan=6)
text.bind("<KeyRelease>", mark_text_edited)

bold_var = tk.BooleanVar()
underline_var = tk.BooleanVar()
tk.Checkbutton(frame, text="Bold", variable=bold_var, command=update_slide).grid(row=1, column=1)
tk.Checkbutton(frame, text="Underline", variable=underline_var, command=update_slide).grid(row=1, column=2)
color_btn = tk.Button(frame, text="Text Color", command=choose_color, bg="#FFFFFF")
color_btn.grid(row=1, column=3)

tk.Button(frame, text="⟵ Back", command=prev_slide).grid(row=2, column=1)
tk.Button(frame, text="Next ⟶", command=next_slide).grid(row=2, column=2)
tk.Button(frame, text="Add Slide", command=add_slide).grid(row=2, column=3)
tk.Button(frame, text="Remove Slide", command=remove_slide).grid(row=2, column=4)
tk.Button(frame, text="Move Up", command=lambda: move_slide(-1)).grid(row=2, column=5)
tk.Button(frame, text="Move Down", command=lambda: move_slide(1)).grid(row=2, column=6)

autosave_label = tk.Label(root, text="", fg="green")
autosave_label.pack(pady=5)

load_slides()
refresh_slide_list()
show_slide()

root.mainloop()