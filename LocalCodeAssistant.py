import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext, filedialog, simpledialog, messagebox
import subprocess
import re
import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
 
# ----------------------------------------------------
# GLOBAL STATE
# ----------------------------------------------------
conversation_history = []
observer = None
current_folder = None
current_file_path = None
last_update_time = 0
 
current_model = "qwen2.5-coder:7b"
 
ALLOWED_EXTENSIONS = (".py", ".cpp", ".cc", ".cxx", ".hpp", ".h")
 
# ----------------------------------------------------
# AI STATUS
# ----------------------------------------------------
def set_ai_status(text):
    window.after(0, lambda: ai_status_label.configure(text=f"AI: {text}"))
 
# ----------------------------------------------------
# FILE WATCHER
# ----------------------------------------------------
class CodeChangeHandler(FileSystemEventHandler):
 
    def on_modified(self, event):
        global last_update_time
 
        if event.is_directory:
            return
 
        if not event.src_path.endswith(ALLOWED_EXTENSIONS):
            return
 
        if time.time() - last_update_time < 0.5:
            return
 
        last_update_time = time.time()
 
        if current_file_path and os.path.abspath(event.src_path) == os.path.abspath(current_file_path):
            window.after(0, load_file_into_editor, current_file_path)
 
 
def start_watching(path):
    global observer
 
    if observer:
        observer.stop()
        observer.join()
 
    observer = Observer()
    observer.schedule(CodeChangeHandler(), path, recursive=True)
    observer.start()
 
# ----------------------------------------------------
# FILE EXPLORER
# ----------------------------------------------------
all_project_files = []  #search filtering
 
 
def load_folder_files(folder, filter_text=""):
    global all_project_files
 
    for widget in file_list_frame.winfo_children():
        widget.destroy()
 
    if not filter_text:
        all_project_files = []
 
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in ["__pycache__", ".git", "venv"]]
 
        for file in files:
            if file.endswith(ALLOWED_EXTENSIONS):
                full_path = os.path.join(root, file)
                rel = os.path.relpath(full_path, folder)
 
                if not filter_text:
                    all_project_files.append((rel, full_path))
 
                if filter_text.lower() not in rel.lower():
                    continue
 
                btn = ctk.CTkButton(file_list_frame, text=rel, anchor="w",
                                    command=lambda p=full_path: load_file_into_editor(p))
                btn.pack(fill="x", padx=2, pady=1)
 
 
def filter_files(event=None):
    if not current_folder:
        return
    query = file_search_var.get()
    for widget in file_list_frame.winfo_children():
        widget.destroy()
    for rel, full_path in all_project_files:
        if query.lower() in rel.lower():
            btn = ctk.CTkButton(file_list_frame, text=rel, anchor="w",
                                command=lambda p=full_path: load_file_into_editor(p))
            btn.pack(fill="x", padx=2, pady=1)
 
 
def load_file_into_editor(path):
    global current_file_path
 
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
 
        editor.delete("1.0", tk.END)
        editor.insert(tk.END, content)
 
        editor.edit_reset()
 
        current_file_path = path
        file_label.configure(text=f"Editing: {os.path.basename(path)}")
 
    except Exception as e:
        print("Error loading file:", e)
 
 
def save_file():
    global current_file_path
 
    if not current_file_path:
        return
 
    try:
        content = editor.get("1.0", tk.END)
 
        with open(current_file_path, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
 
        os.utime(current_file_path, None)
        status_label.configure(text=f"Saved: {current_file_path}")
 
    except Exception as e:
        print("Save error:", e)
 
# ----------------------------------------------------
# CREATE FILE
# ----------------------------------------------------
def create_new_python_file():
 
    if not current_folder:
        messagebox.showinfo("Select Folder", "Please select a folder first.")
        return
 
    filename = simpledialog.askstring("New Python File", "Enter file name:")
 
    if not filename:
        return
 
    if not filename.endswith(".py"):
        filename += ".py"
 
    path = os.path.join(current_folder, filename)
 
    if os.path.exists(path):
        messagebox.showerror("Error", "File already exists.")
        return
 
    with open(path, "w", encoding="utf-8") as f:
        f.write("# New Python file\n\n")
 
    load_folder_files(current_folder)
    load_file_into_editor(path)
 
# ----------------------------------------------------
# DELETE FILE
# ----------------------------------------------------
def delete_current_file():
    global current_file_path
 
    if not current_file_path:
        return
 
    confirm = messagebox.askyesno(
        "Delete File",
        f"Delete {os.path.basename(current_file_path)}?"
    )
 
    if not confirm:
        return
 
    os.remove(current_file_path)
 
    editor.delete("1.0", tk.END)
    file_label.configure(text="No file selected")
 
    load_folder_files(current_folder)
 
# ----------------------------------------------------
# RUN CODE
# ----------------------------------------------------
def run_code():
 
    if not current_file_path:
        return
 
    save_file()
 
    def execute():
 
        output_console.config(state=tk.NORMAL)
        output_console.delete("1.0", tk.END)
 
        ext = os.path.splitext(current_file_path)[1]
 
        try:
 
            if ext == ".py":
 
                result = subprocess.run(
                    ["python", current_file_path],
                    capture_output=True,
                    text=True
                )
 
                output_console.insert(tk.END, result.stdout)
                output_console.insert(tk.END, result.stderr)
 
            elif ext in [".cpp", ".cc", ".cxx"]:
 
                exe = os.path.join(os.path.dirname(current_file_path), "temp.exe")
 
                compile_result = subprocess.run(
                    ["g++", current_file_path, "-o", exe],
                    capture_output=True,
                    text=True
                )
 
                if compile_result.returncode != 0:
                    output_console.insert(tk.END, compile_result.stderr)
                else:
                    run_result = subprocess.run(
                        [exe],
                        capture_output=True,
                        text=True
                    )
 
                    output_console.insert(tk.END, run_result.stdout)
                    output_console.insert(tk.END, run_result.stderr)
 
        except Exception as e:
            output_console.insert(tk.END, str(e))
 
        output_console.config(state=tk.DISABLED)
 
    threading.Thread(target=execute).start()
 
# ----------------------------------------------------
# MODEL SWITCHER
# ----------------------------------------------------
def toggle_model():
    global current_model
 
    if current_model == "qwen2.5-coder:7b":
        current_model = "qwen2.5-coder:14b"
        model_button.configure(text="Switch to 7B")
        model_label.configure(text="Model: 14B")
    else:
        current_model = "qwen2.5-coder:7b"
        model_button.configure(text="Switch to 14B")
        model_label.configure(text="Model: 7B")
 
# ----------------------------------------------------
# STREAMING AI
# ----------------------------------------------------
def ai_query_stream(prompt, on_chunk, on_done):
 
    set_ai_status("Running...")
 
    process = subprocess.Popen(
        ["ollama", "run", current_model],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
 
    process.stdin.write(prompt)
    process.stdin.close()
 
    full = ""
 
    for line in process.stdout:
        full += line
        window.after(0, on_chunk, line)
 
    process.stdout.close()
    process.wait()
 
    set_ai_status("Idle")
    window.after(0, on_done, full)
 
# ----------------------------------------------------
# CODE BLOCK WIDGET
# ----------------------------------------------------
def clean_code_block(code: str) -> str:
    """Remove leading language tag (e.g. 'python', 'cpp') if present as first line."""
    lines = code.split("\n")
    if lines and re.match(r"^\s*(python|cpp|c\+\+|javascript|js|bash|sh|java|ts|typescript|html|css|sql|rust|go)\s*$", lines[0], re.IGNORECASE):
        lines = lines[1:]
    return "\n".join(lines).strip()
 
 
def insert_code_block(parent_frame, code: str):
    """Create a styled code block widget with a Copy button inside the chat scroll area."""
    code = clean_code_block(code)
 
    # Outer contain
    block_frame = tk.Frame(parent_frame, bg="#2b2b2b", bd=0)
    block_frame.pack(fill="x", padx=8, pady=6)
 
    # +Copy button
    header = tk.Frame(block_frame, bg="#3a3a3a")
    header.pack(fill="x")
 
    lang_label = tk.Label(header, text="code", bg="#3a3a3a", fg="#888888",
                          font=("Consolas", 9), padx=8, pady=3)
    lang_label.pack(side="left")
 
    def copy_code():
        window.clipboard_clear()
        window.clipboard_append(code)
        copy_btn.configure(text="Copied!")
        window.after(2000, lambda: copy_btn.configure(text="Copy"))
 
    copy_btn = ctk.CTkButton(
        header, text="Copy", width=60, height=24,
        fg_color="#555555", hover_color="#666666",
        font=("Consolas", 10), command=copy_code
    )
    copy_btn.pack(side="right", padx=4, pady=2)
 
    # Code text area (read only)
    code_text = tk.Text(
        block_frame,
        font=("Consolas", 11),
        bg="#1e1e1e",
        fg="#d4d4d4",
        insertbackground="white",
        relief="flat",
        bd=0,
        wrap=tk.NONE,
        height=min(code.count("\n") + 2, 20),
        state=tk.NORMAL,
        padx=10,
        pady=6,
    )
    code_text.insert(tk.END, code)
    code_text.config(state=tk.DISABLED)
    code_text.pack(fill="x", padx=0, pady=0)
 
 
def render_ai_response(parent_frame, full_text: str):
    """
    Parse the AI response and render plain text + code blocks
    as separate widgets inside parent_frame.
    """
    # Split on ```...``` fences
    parts = re.split(r"```(.*?)```", full_text, flags=re.DOTALL)
 
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Plain text 
            text = part.strip()
            if text:
                lbl = tk.Label(
                    parent_frame,
                    text=text,
                    bg="#1e1e1e",
                    fg="#d4d4d4",
                    font=("Segoe UI", 11),
                    justify="left",
                    anchor="w",
                    wraplength=700,
                )
                lbl.pack(fill="x", padx=12, pady=(4, 0))
        else:
            # Code block 
            insert_code_block(parent_frame, part)
 
# ----------------------------------------------------
# CHAT — with Code Block support
# ----------------------------------------------------
chat_widgets = [] 
 
 
def send_message(event=None):
 
    user_text = user_input_box.get()
 
    if not user_text.strip():
        return
 
    user_input_box.delete(0, tk.END)
 
    # --- User bubble ---
    user_label = tk.Label(
        chat_inner_frame,
        text="You: " + user_text,
        bg="#2c2c54",
        fg="#ffffff",
        font=("Segoe UI", 11),
        justify="left",
        anchor="w",
        wraplength=700,
        padx=10,
        pady=6,
    )
    user_label.pack(fill="x", padx=8, pady=(6, 0))
    chat_widgets.append(user_label)
 
    # --- AI header ---
    ai_header = tk.Label(
        chat_inner_frame,
        text="Code Assistant:",
        bg="#1e1e1e",
        fg="#00ff88",
        font=("Segoe UI", 10, "bold"),
        anchor="w",
        padx=12,
    )
    ai_header.pack(fill="x")
    chat_widgets.append(ai_header)

    stream_buffer = {"text": ""}
 
    # Temp
    streaming_label = tk.Label(
        chat_inner_frame,
        text="",
        bg="#1e1e1e",
        fg="#aaaaaa",
        font=("Consolas", 10),
        justify="left",
        anchor="w",
        wraplength=700,
        padx=12,
    )
    streaming_label.pack(fill="x")
    chat_widgets.append(streaming_label)
 
    def on_chunk(chunk):
        stream_buffer["text"] += chunk
        streaming_label.configure(text=stream_buffer["text"][-300:] + "▌")
        chat_canvas.yview_moveto(1.0)
 
    def on_done(full_text):
        # Remove the temporary streaming label
        streaming_label.destroy()
 
        # Render properly with code blocks
        render_ai_response(chat_inner_frame, full_text)
 
        # Scroll to bottom
        chat_canvas.update_idletasks()
        chat_canvas.yview_moveto(1.0)
 
    prompt = f"""
You are a code assistant.
 
Current code:
{editor.get('1.0', tk.END)}
 
User:
{user_text}
 
Code Assistant:
"""
 
    threading.Thread(target=lambda: ai_query_stream(prompt, on_chunk, on_done)).start()
 
# ----------------------------------------------------
# AI ERROR CHECK + AUTO FIX
# ----------------------------------------------------
def ai_query_once(prompt):
    set_ai_status("Running...")
    result = subprocess.run(
        ["ollama", "run", current_model],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE
    )
    set_ai_status("Idle")
    return result.stdout.decode("utf-8")
 
 
def check_code_errors():
    if not current_file_path:
        messagebox.showinfo("No File", "Please open a file first.")
        return
 
    save_file()
 
    code = editor.get("1.0", tk.END).strip()
    ext = os.path.splitext(current_file_path)[1]
 
    def run_check():
 
        set_ai_status("Testing...")
 
        runtime_error = ""
 
        try:
            if ext == ".py":
                result = subprocess.run(
                    ["python", current_file_path],
                    capture_output=True,
                    text=True
                )
                runtime_error = result.stderr
 
            elif ext in [".cpp", ".cc", ".cxx"]:
                exe = os.path.join(os.path.dirname(current_file_path), "temp_check.exe")
 
                compile_result = subprocess.run(
                    ["g++", current_file_path, "-o", exe],
                    capture_output=True,
                    text=True
                )
 
                if compile_result.returncode != 0:
                    runtime_error = compile_result.stderr
                else:
                    run_result = subprocess.run(
                        [exe],
                        capture_output=True,
                        text=True
                    )
                    runtime_error = run_result.stderr
 
        except Exception as e:
            runtime_error = str(e)
 
        if not runtime_error.strip():
            set_ai_status("Idle")
 
            def ok_ui():
                messagebox.showinfo("Code Check", "Code ran successfully. No errors found.")
            window.after(0, ok_ui)
            return
 
        set_ai_status("Fixing...")
 
        prompt = f"""
Fix this code based on the runtime error.
 
ERROR:
{runtime_error}
 
CODE:
{code}
 
Return ONLY fixed code inside ``` ```
"""
 
        response = ai_query_once(prompt)
 
        match = re.search(r"```(.*?)```", response, re.DOTALL)
 
        def update_ui():
            if match:
                fixed_code = clean_code_block(match.group(1))
                apply = messagebox.askyesno("Apply Fix", "Apply AI fixed code?")
                if apply:
                    editor.delete("1.0", tk.END)
                    editor.insert(tk.END, fixed_code)
 
        window.after(0, update_ui)
 
    threading.Thread(target=run_check).start()
 
# ----------------------------------------------------
# FOLDER
# ----------------------------------------------------
def choose_folder():
 
    global current_folder
 
    folder = filedialog.askdirectory()
 
    if folder:
        current_folder = folder
        load_folder_files(folder)
        start_watching(folder)
        status_label.configure(text=f"Folder: {folder}")
 
# ----------------------------------------------------
# GUI
# ----------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
 
window = ctk.CTk()
window.title("Local Code Assistant")
window.geometry("1300x950")
 
window.rowconfigure(1, weight=1)
window.columnconfigure(0, weight=1)
 
header = ctk.CTkFrame(window, height=60)
header.grid(row=0, column=0, sticky="ew")
 
ctk.CTkLabel(header, text="Local Code Assistant", font=("Segoe UI", 18, "bold")).pack(pady=10)
 
ai_status_label = ctk.CTkLabel(header, text="AI: Idle")
ai_status_label.pack()
 
main_frame = ctk.CTkFrame(window)
main_frame.grid(row=1, column=0, sticky="nsew")
main_frame.rowconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)
 
# LEFT PANEL
file_panel = ctk.CTkFrame(main_frame)
file_panel.grid(row=0, column=0, sticky="ns", padx=5, pady=5)
file_panel.rowconfigure(2, weight=1)
 
file_buttons = ctk.CTkFrame(file_panel)
file_buttons.grid(row=0, column=0, sticky="ew")
 
ctk.CTkButton(file_buttons, text="+", command=create_new_python_file, width=30).pack(side="left", padx=2, pady=2)
ctk.CTkButton(file_buttons, text="-", command=delete_current_file, width=30).pack(side="left", padx=2, pady=2)
 
file_search_var = tk.StringVar()
file_search_entry = ctk.CTkEntry(file_panel, placeholder_text="Search files...", textvariable=file_search_var, width=250)
file_search_entry.grid(row=1, column=0, padx=4, pady=(4, 2), sticky="ew")
file_search_var.trace_add("write", lambda *args: filter_files())
 
file_list_frame = ctk.CTkScrollableFrame(file_panel, width=250)
file_list_frame.grid(row=2, column=0, sticky="ns")
 
# MODEL SWITCH
model_frame = ctk.CTkFrame(file_panel)
model_frame.grid(row=3, column=0, sticky="s")
 
model_label = ctk.CTkLabel(model_frame, text="Model: 7B")
model_label.pack()
 
model_button = ctk.CTkButton(model_frame, text="Switch to 14B", command=toggle_model)
model_button.pack(pady=5)
 
# RIGHT PANEL
right_panel = ctk.CTkFrame(main_frame)
right_panel.grid(row=0, column=1, sticky="nsew")
 
right_panel.rowconfigure(1, weight=1)
right_panel.rowconfigure(3, weight=1)
right_panel.rowconfigure(4, weight=1)
right_panel.columnconfigure(0, weight=1)
 
file_label = ctk.CTkLabel(right_panel, text="No file selected")
file_label.grid(row=0, column=0, sticky="ew")
 
editor = scrolledtext.ScrolledText(
    right_panel, font=("Consolas", 11),
    bg="#1e1e1e", fg="#d4d4d4",
    insertbackground="white", undo=True, maxundo=-1
)
editor.grid(row=1, column=0, sticky="nsew", padx=5)
 
# Undo / Redo I Ctrl+Z and Ctrl+Y
def undo(event=None):
    try:
        editor.edit_undo()
    except tk.TclError:
        pass
    return "break"
 
def redo(event=None):
    try:
        editor.edit_redo()
    except tk.TclError:
        pass
    return "break"
 
editor.bind("<Control-z>", undo)
editor.bind("<Control-y>", redo)
 
buttons = ctk.CTkFrame(right_panel)
buttons.grid(row=2, column=0, sticky="ew")
 
ctk.CTkButton(buttons, text="Save File", command=save_file).pack(side="left", expand=True, fill="x")
ctk.CTkButton(buttons, text="Run", command=run_code).pack(side="left", expand=True, fill="x")
ctk.CTkButton(buttons, text="Check Code", command=check_code_errors).pack(side="left", expand=True, fill="x")
 
output_console = scrolledtext.ScrolledText(
    right_panel, font=("Consolas", 11),
    bg="#111111", fg="#00ff88"
)
output_console.grid(row=3, column=0, sticky="nsew", padx=5)
output_console.config(state=tk.DISABLED)
 
# ----------------------------------------------------
# CHAT AREA
# ----------------------------------------------------
chat_outer = tk.Frame(right_panel, bg="#1e1e1e")
chat_outer.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)
chat_outer.rowconfigure(0, weight=1)
chat_outer.columnconfigure(0, weight=1)
 
chat_canvas = tk.Canvas(chat_outer, bg="#1e1e1e", highlightthickness=0)
chat_canvas.grid(row=0, column=0, sticky="nsew")
 
chat_scrollbar = tk.Scrollbar(chat_outer, orient="vertical", command=chat_canvas.yview)
chat_scrollbar.grid(row=0, column=1, sticky="ns")
chat_canvas.configure(yscrollcommand=chat_scrollbar.set)
 
chat_inner_frame = tk.Frame(chat_canvas, bg="#1e1e1e")
chat_canvas_window = chat_canvas.create_window((0, 0), window=chat_inner_frame, anchor="nw")
 
 
def on_chat_frame_configure(event):
    chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))
 
 
def on_chat_canvas_configure(event):
    chat_canvas.itemconfig(chat_canvas_window, width=event.width)
 
 
chat_inner_frame.bind("<Configure>", on_chat_frame_configure)
chat_canvas.bind("<Configure>", on_chat_canvas_configure)
 
# Mouse wheel scrolling
def on_mousewheel(event):
    chat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
 
chat_canvas.bind_all("<MouseWheel>", on_mousewheel)
 
# ----------------------------------------------------
# INPUT ROW
# ----------------------------------------------------
input_frame = ctk.CTkFrame(right_panel)
input_frame.grid(row=5, column=0, sticky="ew")
input_frame.columnconfigure(0, weight=1)
 
user_input_box = ctk.CTkEntry(input_frame)
user_input_box.grid(row=0, column=0, sticky="ew")
 
ctk.CTkButton(input_frame, text="Ask", command=send_message).grid(row=0, column=1)
ctk.CTkButton(input_frame, text="Select Folder", command=choose_folder).grid(row=0, column=2)
 
window.bind("<Return>", send_message)
 
status_label = ctk.CTkLabel(window, text="No folder selected")
status_label.grid(row=2, column=0, sticky="w")
 
zoom_label = ctk.CTkLabel(window, text="Zoom: 100%")
zoom_label.grid(row=2, column=0, sticky="e", padx=10)
 
# ----------------------------------------------------
# ZOOM
# ----------------------------------------------------
font_size = 11
zoom_percent = 100
 
 
def update_zoom_label():
    zoom_label.configure(text=f"Zoom: {zoom_percent}%")
 
 
def apply_font_size():
    global zoom_percent
    editor.configure(font=("Consolas", font_size))
    output_console.configure(font=("Consolas", font_size))
    zoom_percent = int((font_size / 11) * 100)
    update_zoom_label()
 
 
def zoom_in(event=None):
    global font_size
    font_size += 1
    apply_font_size()
 
 
def zoom_out(event=None):
    global font_size
    if font_size > 6:
        font_size -= 1
        apply_font_size()
 
 
window.bind("<Control-plus>", zoom_in)
window.bind("<Control-equal>", zoom_in)
window.bind("<Control-minus>", zoom_out)
 
apply_font_size()
 
window.mainloop()