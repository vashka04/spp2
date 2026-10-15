#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

TOKENIZER_NAME = "tokenizer.php"

_PHP_EXE = None


def find_php():
    global _PHP_EXE
    if _PHP_EXE is not None:
        return _PHP_EXE

    exe = shutil.which("php")
    if exe:
        _PHP_EXE = exe
        return _PHP_EXE

    if os.path.isfile(r"C:\php\php.exe"):
        _PHP_EXE = r"C:\php\php.exe"
        return _PHP_EXE

    _PHP_EXE = None
    return None


def tokenize_with_php(code: str, php_exe: str, tokenizer_path: str):
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".php", prefix="gilb_")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(code)

        proc = subprocess.run(
            [php_exe, tokenizer_path, tmp_path],
            capture_output=True,
            text=False,          
            check=False,
        )
        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"tokenizer.php завершился с кодом {proc.returncode}:\n{err}"
            )

        out = proc.stdout.decode("utf-8", errors="replace")
        tokens = []
        for raw in out.splitlines():
            if "===" not in raw:
                continue
            name, _, text = raw.partition("===")
            tokens.append((name, text))
        return tokens
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

CONTROL_TOKEN = {
    "T_IF": "if",
    "T_ELSEIF": "elseif",
    "T_FOR": "for",
    "T_FOREACH": "foreach",
    "T_WHILE": "while",
    "T_DO": "do",
    "T_SWITCH": "switch",
    "T_CASE": "case",
    # "T_CATCH": "catch",
    # "T_COALESCE": "coalesce"
}

CONTROL_STATEMENT = {
    "T_IF": "if",
    "T_FOR": "for",
    "T_FOREACH": "foreach",
    "T_WHILE": "while",
    "T_DO": "do",
    "T_SWITCH": "switch"
}

BRACKETS_CONTROL_STATEMENT = {
    "T_IF": "if",
    "T_ELSEIF": "elseif",
    "T_FOR": "for",
    "T_FOREACH": "foreach",
    "T_WHILE": "while",
    "T_SWITCH": "switch"
}

BRACES_CONTROL_STATEMENT = {
    "T_IF": "if",
    "T_ELSEIF": "elseif",
    "T_FOR": "for",
    "T_FOREACH": "foreach",
    "T_WHILE": "while",
    "T_DO": "do",
    "T_SWITCH": "switch",
}

def analyze_tokens(tokens):
    ignored = {
        "T_WHITESPACE", "T_COMMENT", "T_DOC_COMMENT",
        "T_OPEN_TAG", "T_CLOSE_TAG", "T_INLINE_HTML",
        "T_CONSTANT_ENCAPSED_STRING", "T_ENCAPSED_AND_WHITESPACE",
        "T_START_HEREDOC", "T_END_HEREDOC",
    }
    seq = []
    for name, text in tokens:
        if name in ignored:
            print(f"[skip] {name}: {text!r}")
            continue
        seq.append((name, text))

    counts = {
        "if": 0, "elseif": 0, "for": 0, "foreach": 0,
        "while": 0, "do": 0, "switch": 0, "case": 0,
        "default": 0, "catch": 0, "ternary": 0, "coalesce": 0
    }
    for name, text in seq:
        key = CONTROL_TOKEN.get(name)
        if key:
            counts[key] += 1
        elif name == "CHARACTER" and text == "?":
            counts["ternary"] += 1
        elif name == "T_DEFAULT":
            counts["default"] += 1

    # Абсолютная сложность:
    absolute = (
        counts["if"] + counts["elseif"]
        #+ counts["ternary"] + counts["coalesce"]
        + counts["for"] + counts["foreach"] + counts["while"]
        + counts["case"]
    )

    statements = sum(
        1 for name, text in seq if name == "CHARACTER" and text == ";"
    )
    relative = absolute / statements if statements else 0.0


    control_stack = []
    not_control_braces_and_brackets = []
    my_cur_depth = 0
    my_max_depth = 0
    for i, (name, text) in enumerate(seq):
        # обработка закрытия и открытия elseif
        if name == "T_ELSEIF":
            control_stack.append((name, text))
            my_cur_depth += 1
            my_max_depth = max(my_max_depth, my_cur_depth)
            continue
        elif control_stack:
            last_name, last_text = control_stack[-1]
            while last_name == "END_ELSEIF":
                my_cur_depth -= 1
                control_stack.pop()
                if not control_stack:
                    break
                last_name, last_text = control_stack[-1]
            if last_name == "END_IF":
                my_cur_depth -= 1
                control_stack.pop()

        if name not in CONTROL_STATEMENT and not control_stack:
            continue

        #ниже control_stack не пуст

        if name == "CHARACTER" and text == "{":
            last_name, last_text = control_stack[-1]
            if last_name in BRACES_CONTROL_STATEMENT:
                control_stack.append((name, text))
            else:
                not_control_braces_and_brackets.append((name, text))
            continue

        if name == "CHARACTER" and text == "}":
            if not not_control_braces_and_brackets:
                last_control_name, last_control_text = control_stack.pop()
                if last_control_name == "CHARACTER" and last_control_text == "{":
                    last_control_name, last_control_text = control_stack.pop()
                    if last_control_name == "T_ELSEIF":
                        control_stack.append(("END_ELSEIF", ""))
                    elif last_control_name == "T_IF":
                        control_stack.append(("END_IF", ""))
                    elif last_control_name == "T_DO":
                        control_stack.append(("END_DO", ""))
                    else:
                        my_cur_depth -= 1
                elif last_control_name == "T_CASE":
                    my_cur_depth -= 1
                    last_control_name, last_control_text = control_stack[-1]
                    while last_control_name == "T_CASE":
                        my_cur_depth -= 1
                        control_stack.pop()
                        last_control_name, last_control_text = control_stack[-1]
                    control_stack.pop() #очистка от {
                    control_stack.pop() #очистка от switch
                continue

            last_name, last_text = not_control_braces_and_brackets[-1]
            if last_name == "CHARACTER" and last_text == "{":
                not_control_braces_and_brackets.pop()
            else:
                last_control_name, last_control_text = control_stack.pop()
                if last_control_name == "CHARACTER" and last_control_text == "{":
                    last_control_name, last_control_text = control_stack.pop()
                    if last_control_name == "T_ELSEIF":
                        control_stack.append(("END_ELSEIF", ""))
                    elif last_control_name == "T_IF":
                        control_stack.append(("END_IF", ""))
                    elif last_control_name == "T_DO":
                        control_stack.append(("END_DO", ""))
                    else:
                        my_cur_depth -= 1
                elif last_control_name == "T_CASE":
                    my_cur_depth -= 1
                    last_control_name, last_control_text = control_stack[-1]
                    while last_control_name == "T_CASE":
                        my_cur_depth -= 1
                        control_stack.pop()
                        last_control_name, last_control_text = control_stack[-1]
                    control_stack.pop() #очистка от {
                    control_stack.pop() #очистка от switch

            continue


        if name == "CHARACTER" and text == "(":
            last_name, last_text = control_stack[-1]
            if last_name in BRACKETS_CONTROL_STATEMENT:
                control_stack.append((name, text))
            else:
                not_control_braces_and_brackets.append((name, text))
            continue

        if name == "CHARACTER" and text == ")":
            if not not_control_braces_and_brackets:
                control_stack.pop()  # скобка закрывала if (, for(, ...
                continue

            last_name, last_text = not_control_braces_and_brackets[-1]
            if last_name == "CHARACTER" and last_text == "(":
                not_control_braces_and_brackets.pop()
            else:
                control_stack.pop()  # скобка закрывала if (, for(, ...
            continue

        if name == "CHARACTER" and text == ";":
            last_name, last_text = control_stack[-1]
            if last_name == "OPENED_OPERATOR":
                control_stack.pop()
                print(f"[CLOSED] {name}: {text!r}")
            else:
                print(f"[ANOTHER] {name}: {text!r}")
            continue

        if name not in CONTROL_TOKEN:
            last_name, last_text = control_stack[-1]
            if last_name in CONTROL_STATEMENT:
                print(f"[OPENED_OPERATOR] {name}: {text!r}")
                control_stack.append(("OPENED_OPERATOR", text))
            else:
                print(f"[ANOTHER] {name}: {text!r}")
            continue

        if name in ["T_IF", "T_FOR", "T_FOREACH", "T_DO", "T_CASE"]:
            control_stack.append((name, text))
            my_cur_depth += 1
            my_max_depth = max(my_max_depth, my_cur_depth)
            continue

        if name == "T_WHILE":
            last_name, last_text = control_stack[-1]
            if last_name == "END_DO":
                control_stack.pop()
                my_cur_depth -= 1
            else:
                control_stack.append((name, text))
                my_cur_depth += 1
                my_max_depth = max(my_max_depth, my_cur_depth)
            continue

        if name == "T_SWITCH":
            control_stack.append((name, text))
            continue

    return {
        "absolute": absolute,
        "relative": relative,
        "max_depth": my_max_depth,
        "statements": statements,
        "counts": counts,
        "switch_branches": [],
        "case_branches": counts["case"],
    }


# ----------------------------------------------------------------------------
# GUI
# ----------------------------------------------------------------------------

class GilbApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Метрики сложности потока управления — Джилб (PHP-токенизатор)")
        self.geometry("980x720")
        self.minsize(760, 560)

        self.php_exe = find_php()
        self.tokenizer_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), TOKENIZER_NAME)

        self._build()
        self._check_php()
        self.load_default()

    def _build(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Button(top, text="Открыть PHP-файл…", command=self.open_file).pack(side="left")
        ttk.Button(top, text="Анализировать", command=self.analyze).pack(side="left", padx=8)
        ttk.Button(top, text="Загрузить пример", command=self.load_default).pack(side="left")
        self.path_label = ttk.Label(top, text="Код можно редактировать прямо в поле ниже")
        self.path_label.pack(side="left", padx=12)

        self.editor = tk.Text(self, wrap="none", undo=True, font=("Consolas", 10), height=28)
        ybar = ttk.Scrollbar(self, orient="vertical", command=self.editor.yview)
        xbar = ttk.Scrollbar(self, orient="horizontal", command=self.editor.xview)
        self.editor.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        self.editor.pack(fill="both", expand=True, padx=(10, 0), pady=(0, 0), side="left")
        ybar.pack(fill="y", side="right", padx=(0, 10))
        xbar.pack(fill="x", side="bottom", padx=10)

        result = ttk.LabelFrame(self, text="Результаты анализа", padding=10)
        result.pack(fill="x", padx=10, pady=10)
        self.result_label = ttk.Label(result, text="Нажмите «Анализировать».", justify="left")
        self.result_label.pack(anchor="w")
        self.detail_label = ttk.Label(result, text="", justify="left")
        self.detail_label.pack(anchor="w", pady=(6, 0))

    def _check_php(self):
        if self.php_exe is None:
            messagebox.showerror(
                "PHP не найден",
                "Не удалось найти php.exe.\n"
                "Установите PHP и добавьте его в PATH, либо положите php.exe в C:\\php\\."
            )
        elif not os.path.isfile(self.tokenizer_path):
            messagebox.showerror(
                "Нет tokenizer.php",
                f"Не найден файл токенизатора:\n{self.tokenizer_path}"
            )

    def load_default(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input.php")
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", content)
            self.path_label.configure(text="input.php")
        except OSError as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть input.php:\n{e}")

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Выберите PHP-файл",
            filetypes=[("PHP-файлы", "*.php"), ("Все файлы", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                content = f.read()
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", content)
            self.path_label.configure(text=path)
            self.analyze()
        except (OSError, UnicodeError) as e:
            messagebox.showerror("Ошибка чтения", str(e))

    def analyze(self):
        if self.php_exe is None:
            messagebox.showerror("PHP не найден", "Установите PHP и добавьте php.exe в PATH.")
            return
        if not os.path.isfile(self.tokenizer_path):
            messagebox.showerror("Нет tokenizer.php",
                                 f"Не найден файл токенизатора:\n{self.tokenizer_path}")
            return

        code = self.editor.get("1.0", "end-1c")
        try:
            tokens = tokenize_with_php(code, self.php_exe, self.tokenizer_path)
            r = analyze_tokens(tokens)
        except Exception as e:
            messagebox.showerror("Ошибка анализа", str(e))
            return

        self.result_label.configure(text=(
            f"Абсолютная сложность Джилба: {r['absolute']}\n"
            f"Относительная сложность: {r['relative']:.4f} "
            f"({r['relative']*100:.2f}%)\n"
            f"Максимальный уровень вложенности: {r['max_depth']}"
        ))
        c = r["counts"]
        self.detail_label.configure(text=(
            f"if={c['if']}, elseif={c['elseif']}, for={c['for']}, \n"
            f"foreach={c['foreach']}, while={c['while']}, case={c['case']}, \n"
            #f"ternary={c['ternary']}, coalesce={c['coalesce']}, \n"
            f"операторов={r['statements']}"
        ))

if __name__ == "__main__":
    GilbApp().mainloop()