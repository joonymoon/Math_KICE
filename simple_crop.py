"""
간단한 크롭 도구 - 확실하게 크롭됩니다
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os


class SimpleCropTool:
    def __init__(self, root):
        self.root = root
        self.root.title("간단한 크롭 도구")
        self.root.geometry("1400x900")

        # State
        self.original_image = None
        self.display_image = None
        self.cropped_image = None  # 크롭된 결과
        self.photo = None
        self.scale = 1.0
        self.crop_start = None
        self.crop_end = None
        self.rect_id = None

        self.setup_ui()

    def setup_ui(self):
        # Top controls
        top_frame = tk.Frame(self.root, bg='#2c3e50', pady=15)
        top_frame.pack(fill=tk.X)

        btn_style = {'font': ('Arial', 13, 'bold'), 'padx': 25, 'pady': 8}

        tk.Button(top_frame, text="1️⃣ 이미지 열기", command=self.load_image,
                 bg='#27ae60', fg='white', **btn_style).pack(side=tk.LEFT, padx=10)

        tk.Button(top_frame, text="2️⃣ 영역 선택 → 크롭", command=self.do_crop,
                 bg='#3498db', fg='white', **btn_style).pack(side=tk.LEFT, padx=10)

        tk.Button(top_frame, text="3️⃣ 저장", command=self.save_image,
                 bg='#e74c3c', fg='white', **btn_style).pack(side=tk.LEFT, padx=10)

        tk.Button(top_frame, text="🔄 다시 시작", command=self.reset,
                 bg='#95a5a6', fg='white', **btn_style).pack(side=tk.LEFT, padx=10)

        # Status
        self.status_label = tk.Label(top_frame, text="이미지를 열어주세요",
                                     font=('Arial', 11), bg='#2c3e50', fg='white')
        self.status_label.pack(side=tk.LEFT, padx=30)

        # Main area - split view
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left - Original with selection
        left_frame = tk.LabelFrame(main_frame, text="원본 (마우스로 드래그하여 영역 선택)",
                                   font=('Arial', 12, 'bold'), fg='#2c3e50')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.canvas = tk.Canvas(left_frame, bg='#ecf0f1', cursor='cross')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # Right - Cropped preview
        right_frame = tk.LabelFrame(main_frame, text="크롭 결과 미리보기",
                                    font=('Arial', 12, 'bold'), fg='#2c3e50')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        self.preview_canvas = tk.Canvas(right_frame, bg='#ecf0f1')
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        # Instructions
        instructions = tk.Label(
            self.root,
            text="📝 사용법: 1) 이미지 열기 → 2) 마우스로 드래그하여 영역 선택 → 3) 크롭 버튼 클릭 → 4) 저장",
            font=('Arial', 11, 'bold'),
            bg='#3498db',
            fg='white',
            pady=12
        )
        instructions.pack(fill=tk.X, side=tk.BOTTOM)

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="이미지 파일 선택",
            filetypes=[("이미지 파일", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )

        if not file_path:
            return

        try:
            self.original_image = Image.open(file_path)
            self.cropped_image = None  # Reset cropped
            self.display_original()
            self.clear_preview()
            self.status_label.config(
                text=f"✅ {os.path.basename(file_path)} ({self.original_image.width}x{self.original_image.height})"
            )
        except Exception as e:
            messagebox.showerror("오류", f"이미지를 열 수 없습니다:\n{e}")

    def display_original(self):
        if not self.original_image:
            return

        # Fit to canvas
        canvas_w = max(self.canvas.winfo_width(), 600)
        canvas_h = max(self.canvas.winfo_height(), 400)

        scale_w = canvas_w / self.original_image.width
        scale_h = canvas_h / self.original_image.height
        self.scale = min(scale_w, scale_h, 1.0)

        w = int(self.original_image.width * self.scale)
        h = int(self.original_image.height * self.scale)

        self.display_image = self.original_image.resize((w, h), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.display_image)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

    def clear_preview(self):
        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(
            300, 200,
            text="크롭 버튼을 눌러\n결과를 확인하세요",
            font=('Arial', 16),
            fill='#7f8c8d'
        )

    def on_mouse_down(self, event):
        if not self.original_image:
            return
        self.crop_start = (event.x, event.y)

    def on_mouse_drag(self, event):
        if not self.original_image or not self.crop_start:
            return

        if self.rect_id:
            self.canvas.delete(self.rect_id)

        self.rect_id = self.canvas.create_rectangle(
            self.crop_start[0], self.crop_start[1],
            event.x, event.y,
            outline='#e74c3c', width=4
        )

    def on_mouse_up(self, event):
        if not self.original_image or not self.crop_start:
            return
        self.crop_end = (event.x, event.y)

        # Show info
        x1 = int(min(self.crop_start[0], self.crop_end[0]) / self.scale)
        y1 = int(min(self.crop_start[1], self.crop_end[1]) / self.scale)
        x2 = int(max(self.crop_start[0], self.crop_end[0]) / self.scale)
        y2 = int(max(self.crop_start[1], self.crop_end[1]) / self.scale)

        self.status_label.config(
            text=f"선택 완료: ({x1}, {y1}) → ({x2}, {y2}) | {x2-x1}x{y2-y1}px | 크롭 버튼 클릭"
        )

    def do_crop(self):
        if not self.original_image:
            messagebox.showwarning("경고", "먼저 이미지를 열어주세요")
            return

        if not self.crop_start or not self.crop_end:
            messagebox.showwarning("경고", "마우스로 드래그하여 영역을 선택하세요")
            return

        # Calculate crop box
        x1 = int(min(self.crop_start[0], self.crop_end[0]) / self.scale)
        y1 = int(min(self.crop_start[1], self.crop_end[1]) / self.scale)
        x2 = int(max(self.crop_start[0], self.crop_end[0]) / self.scale)
        y2 = int(max(self.crop_start[1], self.crop_end[1]) / self.scale)

        # Validate
        if x2 - x1 < 10 or y2 - y1 < 10:
            messagebox.showwarning("경고", "선택 영역이 너무 작습니다")
            return

        # CROP!
        self.cropped_image = self.original_image.crop((x1, y1, x2, y2))

        # Show preview
        self.show_preview()

        self.status_label.config(
            text=f"✅ 크롭 완료! {self.cropped_image.width}x{self.cropped_image.height}px | 저장 버튼 클릭"
        )
        messagebox.showinfo("완료", f"크롭 성공!\n크기: {self.cropped_image.width} x {self.cropped_image.height}\n\n저장 버튼을 눌러 파일로 저장하세요.")

    def show_preview(self):
        if not self.cropped_image:
            return

        # Fit to preview canvas
        canvas_w = max(self.preview_canvas.winfo_width(), 600)
        canvas_h = max(self.preview_canvas.winfo_height(), 400)

        scale_w = canvas_w / self.cropped_image.width
        scale_h = canvas_h / self.cropped_image.height
        preview_scale = min(scale_w, scale_h, 1.0)

        w = int(self.cropped_image.width * preview_scale)
        h = int(self.cropped_image.height * preview_scale)

        preview_img = self.cropped_image.resize((w, h), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(preview_img)

        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            canvas_w // 2, canvas_h // 2,
            anchor=tk.CENTER,
            image=self.preview_photo
        )

    def save_image(self):
        if not self.cropped_image:
            messagebox.showwarning("경고", "먼저 크롭 버튼을 눌러 이미지를 크롭하세요")
            return

        file_path = filedialog.asksaveasfilename(
            title="크롭된 이미지 저장",
            defaultextension=".png",
            filetypes=[("PNG 파일", "*.png"), ("JPEG 파일", "*.jpg")]
        )

        if not file_path:
            return

        try:
            self.cropped_image.save(file_path)
            messagebox.showinfo("성공", f"저장 완료!\n\n파일: {file_path}\n크기: {self.cropped_image.width} x {self.cropped_image.height}")
            self.status_label.config(text=f"💾 저장됨: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패:\n{e}")

    def reset(self):
        if not self.original_image:
            return

        self.cropped_image = None
        self.crop_start = None
        self.crop_end = None
        self.rect_id = None
        self.display_original()
        self.clear_preview()
        self.status_label.config(text="초기화 완료 - 다시 영역을 선택하세요")


if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleCropTool(root)
    root.mainloop()
