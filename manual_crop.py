"""
Manual Crop Tool - 수동 이미지 크롭 도구
마우스로 드래그하여 영역 선택 후 크롭
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
from pathlib import Path


class ManualCropTool:
    def __init__(self, root):
        self.root = root
        self.root.title("수동 크롭 도구 - Manual Crop Tool")
        self.root.geometry("1200x800")

        # State
        self.image = None
        self.photo = None
        self.original_image = None
        self.scale = 1.0
        self.crop_start = None
        self.crop_end = None
        self.rect_id = None

        # UI Setup
        self.setup_ui()

    def setup_ui(self):
        # Top frame - controls
        top_frame = tk.Frame(self.root, bg='#f0f0f0', pady=10)
        top_frame.pack(fill=tk.X)

        tk.Button(top_frame, text="📁 이미지 열기", command=self.load_image,
                 bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'),
                 padx=20, pady=5).pack(side=tk.LEFT, padx=10)

        tk.Button(top_frame, text="✂️ 크롭하기", command=self.crop_image,
                 bg='#2196F3', fg='white', font=('Arial', 12, 'bold'),
                 padx=20, pady=5).pack(side=tk.LEFT, padx=10)

        tk.Button(top_frame, text="💾 저장하기", command=self.save_cropped,
                 bg='#FF9800', fg='white', font=('Arial', 12, 'bold'),
                 padx=20, pady=5).pack(side=tk.LEFT, padx=10)

        tk.Button(top_frame, text="🔄 초기화", command=self.reset,
                 bg='#9E9E9E', fg='white', font=('Arial', 12, 'bold'),
                 padx=20, pady=5).pack(side=tk.LEFT, padx=10)

        # Info label
        self.info_label = tk.Label(top_frame, text="이미지를 열어주세요",
                                   font=('Arial', 10), bg='#f0f0f0')
        self.info_label.pack(side=tk.LEFT, padx=20)

        # Canvas for image
        self.canvas = tk.Canvas(self.root, bg='white', cursor='cross')
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # Instructions
        instructions = tk.Label(self.root,
                               text="사용법: 마우스로 드래그하여 영역 선택 → 크롭하기 클릭 → 저장하기",
                               font=('Arial', 10), bg='#e3f2fd', pady=10)
        instructions.pack(fill=tk.X)

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="이미지 파일 선택",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )

        if not file_path:
            return

        try:
            self.original_image = Image.open(file_path)
            self.image = self.original_image.copy()
            self.display_image()
            self.info_label.config(text=f"열림: {os.path.basename(file_path)} ({self.image.width}x{self.image.height})")
        except Exception as e:
            messagebox.showerror("오류", f"이미지를 열 수 없습니다: {e}")

    def display_image(self):
        if not self.image:
            return

        # Calculate scale to fit canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 1000
            canvas_height = 700

        scale_w = canvas_width / self.image.width
        scale_h = canvas_height / self.image.height
        self.scale = min(scale_w, scale_h, 1.0)  # Don't upscale

        display_width = int(self.image.width * self.scale)
        display_height = int(self.image.height * self.scale)

        # Resize for display
        display_image = self.image.resize((display_width, display_height), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(display_image)

        # Clear canvas and show image
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.config(scrollregion=(0, 0, display_width, display_height))

    def on_mouse_down(self, event):
        if not self.image:
            return
        self.crop_start = (event.x, event.y)

    def on_mouse_drag(self, event):
        if not self.image or not self.crop_start:
            return

        # Remove previous rectangle
        if self.rect_id:
            self.canvas.delete(self.rect_id)

        # Draw new rectangle
        self.rect_id = self.canvas.create_rectangle(
            self.crop_start[0], self.crop_start[1],
            event.x, event.y,
            outline='red', width=3
        )

    def on_mouse_up(self, event):
        if not self.image or not self.crop_start:
            return
        self.crop_end = (event.x, event.y)

        # Show coordinates
        x1 = int(min(self.crop_start[0], self.crop_end[0]) / self.scale)
        y1 = int(min(self.crop_start[1], self.crop_end[1]) / self.scale)
        x2 = int(max(self.crop_start[0], self.crop_end[0]) / self.scale)
        y2 = int(max(self.crop_start[1], self.crop_end[1]) / self.scale)

        self.info_label.config(
            text=f"선택 영역: ({x1}, {y1}) → ({x2}, {y2}) | 크기: {x2-x1}x{y2-y1}"
        )

    def crop_image(self):
        if not self.image or not self.crop_start or not self.crop_end:
            messagebox.showwarning("경고", "먼저 영역을 선택하세요")
            return

        # Convert display coordinates to original image coordinates
        x1 = int(min(self.crop_start[0], self.crop_end[0]) / self.scale)
        y1 = int(min(self.crop_start[1], self.crop_end[1]) / self.scale)
        x2 = int(max(self.crop_start[0], self.crop_end[0]) / self.scale)
        y2 = int(max(self.crop_start[1], self.crop_end[1]) / self.scale)

        # Crop
        self.image = self.original_image.crop((x1, y1, x2, y2))
        self.display_image()

        # Reset selection
        self.crop_start = None
        self.crop_end = None
        self.rect_id = None

        self.info_label.config(text=f"크롭 완료! 크기: {self.image.width}x{self.image.height}")
        messagebox.showinfo("완료", "크롭이 완료되었습니다!\n저장하기 버튼을 눌러 저장하세요.")

    def save_cropped(self):
        if not self.image:
            messagebox.showwarning("경고", "크롭할 이미지가 없습니다")
            return

        file_path = filedialog.asksaveasfilename(
            title="크롭된 이미지 저장",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            self.image.save(file_path)
            messagebox.showinfo("성공", f"저장 완료!\n{file_path}")
            self.info_label.config(text=f"저장됨: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패: {e}")

    def reset(self):
        if not self.original_image:
            return
        self.image = self.original_image.copy()
        self.display_image()
        self.crop_start = None
        self.crop_end = None
        self.rect_id = None
        self.info_label.config(text="초기화 완료")


if __name__ == "__main__":
    root = tk.Tk()
    app = ManualCropTool(root)
    root.mainloop()
