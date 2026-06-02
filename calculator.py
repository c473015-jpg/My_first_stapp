import tkinter as tk
from tkinter import messagebox
import math
import re

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("계산기")
        self.root.geometry("350x520")
        self.root.minsize(320, 480)
        
        # 계산기 상태 변수
        self.expression = ""
        self.current_input = "0"
        self.is_result_shown = False
        self.history = []
        self.history_visible = False
        
        # 메인 레이아웃 및 기록 패널 생성 (표준 위젯 사용)
        self.create_widgets()
        
        # 키보드 입력 바인딩
        self.root.bind("<Key>", self.handle_keyboard)
        
        # macOS 윈도우 렌더링 강제 활성화 및 포커스 부여
        self.root.update_idletasks()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def create_widgets(self):
        # 1. 메인 계산기 프레임 (좌측)
        self.calc_frame = tk.Frame(self.root)
        self.calc_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # 타이틀바 및 기록 버튼
        top_bar = tk.Frame(self.calc_frame)
        top_bar.pack(fill="x", pady=(0, 5))
        
        title_label = tk.Label(top_bar, text="계산기", font=("Helvetica Neue", 15, "bold"))
        title_label.pack(side="left")
        
        self.history_btn = tk.Button(top_bar, text="🕒 기록", font=("Helvetica Neue", 11), command=self.toggle_history)
        self.history_btn.pack(side="right")
        
        # 디스플레이 영역 (수식 라벨 + 입력창)
        display_frame = tk.LabelFrame(self.calc_frame, text="입력 / 결과", font=("Helvetica Neue", 9))
        display_frame.pack(fill="x", pady=5)
        
        self.formula_label = tk.Label(
            display_frame, 
            text="", 
            font=("Helvetica Neue", 11), 
            anchor="e", 
            fg="gray",
            height=1
        )
        self.formula_label.pack(fill="x", padx=5, pady=(2, 0))
        
        self.result_label = tk.Label(
            display_frame, 
            text="0", 
            font=("Helvetica Neue", 28, "bold"), 
            anchor="e",
            height=1
        )
        self.result_label.pack(fill="x", padx=5, pady=(0, 5))
        
        # 키패드 버튼 영역 (그리드)
        keypad_frame = tk.Frame(self.calc_frame)
        keypad_frame.pack(fill="both", expand=True, pady=5)
        
        for r in range(7):
            keypad_frame.rowconfigure(r, weight=1)
        for c in range(4):
            keypad_frame.columnconfigure(c, weight=1)
            
        # 버튼 배치 (행, 열, 텍스트, 기능 함수)
        buttons = [
            # 0행: 괄호 및 제곱/제곱근
            (0, 0, "(", lambda: self.press_char("(")),
            (0, 1, ")", lambda: self.press_char(")")),
            (0, 2, "x²", lambda: self.press_advanced("square")),
            (0, 3, "√", lambda: self.press_advanced("sqrt")),
            
            # 1행: 삭제 및 나누기
            (1, 0, "C", self.press_clear),
            (1, 1, "CE", self.press_clear_entry),
            (1, 2, "⌫", self.press_backspace),
            (1, 3, "÷", lambda: self.press_operator("÷")),
            
            # 2행: 7, 8, 9, 곱하기
            (2, 0, "7", lambda: self.press_num("7")),
            (2, 1, "8", lambda: self.press_num("8")),
            (2, 2, "9", lambda: self.press_num("9")),
            (2, 3, "×", lambda: self.press_operator("×")),
            
            # 3행: 4, 5, 6, 빼기
            (3, 0, "4", lambda: self.press_num("4")),
            (3, 1, "5", lambda: self.press_num("5")),
            (3, 2, "6", lambda: self.press_num("6")),
            (3, 3, "−", lambda: self.press_operator("−")),
            
            # 4행: 1, 2, 3, 더하기
            (4, 0, "1", lambda: self.press_num("1")),
            (4, 1, "2", lambda: self.press_num("2")),
            (4, 2, "3", lambda: self.press_num("3")),
            (4, 3, "+", lambda: self.press_operator("+")),
            
            # 5행: 역수, 나머지, 부호전환, 소수점
            (5, 0, "1/x", lambda: self.press_advanced("reciprocal")),
            (5, 1, "%", lambda: self.press_operator("%")),
            (5, 2, "+/−", self.press_negate),
            (5, 3, ".", self.press_dot),
            
            # 6행: 넓은 0 버튼 및 계산 실행
            (6, 0, "0", lambda: self.press_num("0")),
            (6, 3, "=", self.press_equal)
        ]
        
        for row, col, text, cmd in buttons:
            column_span = 1
            if text == "0":
                column_span = 3
                
            btn = tk.Button(
                keypad_frame, 
                text=text, 
                font=("Helvetica Neue", 14, "bold" if text in "0123456789.=" else "normal"),
                command=cmd
            )
            btn.grid(row=row, column=col, columnspan=column_span, sticky="nsew", padx=2, pady=2)
            
        # 2. 기록 패널 프레임 (우측, 기본은 숨겨짐)
        self.history_frame = tk.Frame(self.root, width=200)
        
        hist_title = tk.Label(self.history_frame, text="계산 기록", font=("Helvetica Neue", 12, "bold"))
        hist_title.pack(anchor="w", padx=10, pady=5)
        
        # 기록용 리스트박스 및 스크롤바
        list_frame = tk.Frame(self.history_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.history_listbox = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set, 
            font=("Helvetica Neue", 11)
        )
        self.history_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.history_listbox.yview)
        
        # 더블 클릭 시 해당 수식 복원
        self.history_listbox.bind("<Double-Button-1>", self.load_history_item)
        
        clear_hist_btn = tk.Button(
            self.history_frame, 
            text="기록 지우기", 
            font=("Helvetica Neue", 11),
            command=self.clear_history_log
        )
        clear_hist_btn.pack(fill="x", padx=10, pady=5)

    def toggle_history(self):
        if self.history_visible:
            self.history_frame.pack_forget()
            self.history_visible = False
            self.root.geometry(f"350x{self.root.winfo_height()}")
        else:
            self.history_frame.pack(side="right", fill="both", expand=False, padx=10, pady=10)
            self.history_visible = True
            self.root.geometry(f"570x{self.root.winfo_height()}")
            self.update_history_ui()
        self.root.update_idletasks()

    def update_history_ui(self):
        self.history_listbox.delete(0, tk.END)
        for expr, res in self.history:
            self.history_listbox.insert(tk.END, f"{expr} = {res}")
        # 항상 최하단으로 스크롤
        self.history_listbox.yview_moveto(1.0)

    def load_history_item(self, event):
        selection = self.history_listbox.curselection()
        if selection:
            idx = selection[0]
            expr, res = self.history[idx]
            self.expression = expr
            self.current_input = res
            self.is_result_shown = True
            self.update_display()

    def clear_history_log(self):
        self.history.clear()
        self.update_history_ui()

    def update_display(self):
        ui_expression = self.expression
        ui_expression = ui_expression.replace("*", " × ").replace("/", " ÷ ").replace("-", " − ")
        self.formula_label.config(text=ui_expression)
        
        display_txt = self.current_input
        if len(display_txt) > 13:
            try:
                val = float(display_txt)
                display_txt = f"{val:.6e}"
            except ValueError:
                pass
        self.result_label.config(text=display_txt)

    def press_num(self, num):
        if self.is_result_shown:
            self.current_input = num
            self.is_result_shown = False
        else:
            if self.current_input == "0":
                self.current_input = num
            else:
                self.current_input += num
        self.update_display()

    def press_dot(self):
        if self.is_result_shown:
            self.current_input = "0."
            self.is_result_shown = False
        else:
            if "." not in self.current_input:
                self.current_input += "."
        self.update_display()

    def press_char(self, char):
        if self.is_result_shown:
            self.expression = ""
            self.is_result_shown = False
            
        if self.current_input != "0" and char == "(":
            self.expression += self.current_input + "*" + char
            self.current_input = "0"
        elif self.current_input != "0":
            self.expression += self.current_input + char
            self.current_input = "0"
        else:
            self.expression += char
            
        self.update_display()

    def press_operator(self, op):
        eval_op = op
        if op == "×":
            eval_op = "*"
        elif op == "÷":
            eval_op = "/"
        elif op == "−":
            eval_op = "-"
            
        if self.is_result_shown:
            self.expression = self.current_input + eval_op
            self.is_result_shown = False
        else:
            self.expression += self.current_input + eval_op
            
        self.current_input = "0"
        self.update_display()

    def press_negate(self):
        if self.current_input != "0":
            if self.current_input.startswith("-"):
                self.current_input = self.current_input[1:]
            else:
                self.current_input = "-" + self.current_input
            self.update_display()

    def press_clear(self):
        self.expression = ""
        self.current_input = "0"
        self.is_result_shown = False
        self.update_display()

    def press_clear_entry(self):
        self.current_input = "0"
        self.update_display()

    def press_backspace(self):
        if not self.is_result_shown:
            if len(self.current_input) > 1:
                self.current_input = self.current_input[:-1]
            else:
                self.current_input = "0"
            self.update_display()

    def press_advanced(self, op_type):
        try:
            val = float(self.current_input)
            if op_type == "square":
                res_val = val ** 2
                expr_desc = f"sqr({self.current_input})"
            elif op_type == "sqrt":
                if val < 0:
                    raise ValueError("음수의 제곱근은 계산할 수 없습니다.")
                res_val = math.sqrt(val)
                expr_desc = f"√({self.current_input})"
            elif op_type == "reciprocal":
                if val == 0:
                    raise ZeroDivisionError("0으로 나눌 수 없습니다.")
                res_val = 1 / val
                expr_desc = f"1/({self.current_input})"
            else:
                return
                
            if res_val.is_integer():
                res_str = str(int(res_val))
            else:
                res_str = f"{res_val:.10g}"
                
            self.expression = expr_desc
            self.current_input = res_str
            self.is_result_shown = True
            
            self.history.append((expr_desc, res_str))
            if self.history_visible:
                self.update_history_ui()
                
        except Exception as e:
            self.current_input = "Error"
            self.is_result_shown = True
            messagebox.showerror("오류", str(e))
            
        self.update_display()

    def press_equal(self):
        if not self.expression and self.is_result_shown:
            return
            
        eval_expr = self.expression + self.current_input
        
        # 괄호 수동 맞춤
        open_count = eval_expr.count("(")
        close_count = eval_expr.count(")")
        if open_count > close_count:
            eval_expr += ")" * (open_count - close_count)
            
        cleaned_expr = eval_expr.replace(" ", "")
        if not re.match(r"^[0-9+\-*/().%]*$", cleaned_expr):
            self.current_input = "Error"
            self.is_result_shown = True
            self.update_display()
            return
            
        try:
            result = eval(cleaned_expr)
            if isinstance(result, float) and result.is_integer():
                result_str = str(int(result))
            else:
                result_str = f"{result:.10g}"
                
            self.history.append((eval_expr, result_str))
            if self.history_visible:
                self.update_history_ui()
                
            self.expression = ""
            self.current_input = result_str
            self.is_result_shown = True
            
        except ZeroDivisionError:
            self.current_input = "Error"
            self.expression = ""
            self.is_result_shown = True
            messagebox.showerror("오류", "0으로 나눌 수 없습니다.")
        except Exception:
            self.current_input = "Error"
            self.expression = ""
            self.is_result_shown = True
            messagebox.showerror("오류", "수식이 올바르지 않습니다.")
            
        self.update_display()

    def handle_keyboard(self, event):
        char = event.char
        keysym = event.keysym
        
        if char in "0123456789":
            self.press_num(char)
        elif char == ".":
            self.press_dot()
        elif char == "+":
            self.press_operator("+")
        elif char == "-":
            self.press_operator("−")
        elif char == "*":
            self.press_operator("×")
        elif char == "/":
            self.press_operator("÷")
        elif char == "%":
            self.press_operator("%")
        elif char in "()":
            self.press_char(char)
        elif keysym in ("Return", "KP_Enter") or char == "=":
            self.press_equal()
        elif keysym == "BackSpace":
            self.press_backspace()
        elif keysym == "Escape":
            self.press_clear()


if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
