from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd


DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILE = DATA_DIR / "course_selection.xlsx"

COURSE_COLUMNS = ["课程编号", "课程名称", "课程类别", "开课学院", "课程容量", "已选人数"]
RECORD_COLUMNS = [
    "课程编号", "课程名称", "课程类别", "开课学院",
    "操作类型", "操作人", "操作时间", "操作数量"
]
ENROLL_COLUMNS = ["学号", "课程编号", "数量"]
STOPPED_COLUMNS = COURSE_COLUMNS + ["停开时间"]


SAMPLE_COURSES = [
    ["PUB1001", "思想道德与法治", "公共必修", "马克思主义学院", 120, 0],
    ["PUB1002", "大学英语", "公共必修", "外国语学院", 80, 0],
    ["CS2001", "数据结构", "专业核心", "信息学院", 70, 0],
    ["CS2002", "数据库系统概论", "专业核心", "信息学院", 70, 0],
    ["CS3001", "机器学习导论", "专业选修", "信息学院", 60, 0],
    ["FIN2001", "公司金融", "专业核心", "财政金融学院", 65, 0],
    ["GEN1001", "艺术鉴赏", "通识选修", "艺术学院", 100, 0],
    ["PE1001", "羽毛球", "体育专项", "体育部", 30, 0],
]


def _empty_df(columns):
    return pd.DataFrame(columns=columns)


def _normalize_course_id(course_id: str) -> str:
    return str(course_id).strip().upper()


def _normalize_student_id(student_id: str) -> str:
    return str(student_id).strip()


@dataclass
class DateRange:
    start: Optional[pd.Timestamp] = None
    end: Optional[pd.Timestamp] = None


class CourseSelectionSystem:
    """基于 Excel 文件持久化的校园课程选课管理系统。"""

    def __init__(self, data_file: Path = DATA_FILE):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_data_file()

    # -------------------- 文件读写 --------------------

    def _ensure_data_file(self):
        if self.data_file.exists():
            return
        courses = pd.DataFrame(SAMPLE_COURSES, columns=COURSE_COLUMNS)
        records = _empty_df(RECORD_COLUMNS)
        enrollments = _empty_df(ENROLL_COLUMNS)
        stopped = _empty_df(STOPPED_COLUMNS)
        self._save_all(courses, records, enrollments, stopped)

    def _load_all(self):
        try:
            xls = pd.ExcelFile(self.data_file)
            courses = pd.read_excel(xls, "courses")
            records = pd.read_excel(xls, "records")
            enrollments = pd.read_excel(xls, "enrollments")
            stopped = pd.read_excel(xls, "stopped_courses")
        except Exception as e:
            raise RuntimeError(f"读取数据文件失败：{e}")

        # 保证空表也具有正确列结构
        courses = courses.reindex(columns=COURSE_COLUMNS)
        records = records.reindex(columns=RECORD_COLUMNS)
        enrollments = enrollments.reindex(columns=ENROLL_COLUMNS)
        stopped = stopped.reindex(columns=STOPPED_COLUMNS)

        # 类型规整
        for col in ["课程编号", "课程名称", "课程类别", "开课学院"]:
            if col in courses.columns:
                courses[col] = courses[col].astype(str)
        for col in ["课程容量", "已选人数"]:
            courses[col] = pd.to_numeric(courses[col], errors="coerce").fillna(0).astype(int)

        if not records.empty:
            records["操作时间"] = pd.to_datetime(records["操作时间"], errors="coerce")
            records["操作数量"] = pd.to_numeric(records["操作数量"], errors="coerce").fillna(0).astype(int)
            for col in ["课程编号", "课程名称", "课程类别", "开课学院", "操作类型", "操作人"]:
                records[col] = records[col].astype(str)

        if not enrollments.empty:
            enrollments["数量"] = pd.to_numeric(enrollments["数量"], errors="coerce").fillna(0).astype(int)
            enrollments["学号"] = enrollments["学号"].astype(str)
            enrollments["课程编号"] = enrollments["课程编号"].astype(str)

        if not stopped.empty:
            stopped["停开时间"] = pd.to_datetime(stopped["停开时间"], errors="coerce")

        return courses, records, enrollments, stopped

    def _save_all(self, courses, records, enrollments, stopped):
        """
        原子写入：先写临时文件，再替换正式文件。
        避免程序写到一半异常导致 Excel 损坏。
        """
        tmp_path = self.data_file.with_name(self.data_file.stem + ".tmp.xlsx")
        try:
            with pd.ExcelWriter(tmp_path, engine="openpyxl", datetime_format="yyyy-mm-dd hh:mm:ss") as writer:
                courses.to_excel(writer, sheet_name="courses", index=False)
                records.to_excel(writer, sheet_name="records", index=False)
                enrollments.to_excel(writer, sheet_name="enrollments", index=False)
                stopped.to_excel(writer, sheet_name="stopped_courses", index=False)
            os.replace(tmp_path, self.data_file)
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    # -------------------- 课程目录 --------------------

    def list_courses(self) -> pd.DataFrame:
        """按课程类别分组、组内按课程编号升序返回。"""
        courses, _, _, _ = self._load_all()
        if courses.empty:
            return courses

        category_order = {
            "公共必修": 1,
            "专业核心": 2,
            "专业选修": 3,
            "通识选修": 4,
            "体育专项": 5,
        }
        result = courses.copy()
        result["_类别顺序"] = result["课程类别"].map(category_order).fillna(999)
        result = result.sort_values(["_类别顺序", "课程编号"], ascending=[True, True])
        return result.drop(columns=["_类别顺序"]).reset_index(drop=True)

    # -------------------- 选课 / 退课 --------------------

    def enroll(self, student_id: str, course_id: str, quantity: int = 1):
        student_id = _normalize_student_id(student_id)
        course_id = _normalize_course_id(course_id)
        quantity = int(quantity)

        if not student_id:
            raise ValueError("学号不能为空。")
        if quantity <= 0:
            raise ValueError("选课数量必须为正整数。")

        courses, records, enrollments, stopped = self._load_all()
        idx = courses.index[courses["课程编号"].str.upper() == course_id].tolist()
        if not idx:
            raise ValueError(f"课程 {course_id} 不存在或已停开。")

        i = idx[0]
        capacity = int(courses.at[i, "课程容量"])
        selected = int(courses.at[i, "已选人数"])
        if selected + quantity > capacity:
            raise ValueError(
                f"选课失败：课程容量为 {capacity}，当前已选 {selected}，"
                f"仅剩 {capacity - selected} 个名额。"
            )

        course = courses.loc[i]
        courses.at[i, "已选人数"] = selected + quantity

        # 维护当前选课状态：同一学生-课程用数量累计
        mask = (
            enrollments["学号"].astype(str).eq(student_id)
            & enrollments["课程编号"].astype(str).str.upper().eq(course_id)
        )
        if mask.any():
            j = enrollments.index[mask][0]
            enrollments.at[j, "数量"] = int(enrollments.at[j, "数量"]) + quantity
        else:
            enrollments.loc[len(enrollments)] = [student_id, course_id, quantity]

        # 日志快照课程类别与学院，课程以后即使停开也能按类别/学院做历史统计
        new_record = {
            "课程编号": course["课程编号"],
            "课程名称": course["课程名称"],
            "课程类别": course["课程类别"],
            "开课学院": course["开课学院"],
            "操作类型": "选课",
            "操作人": student_id,
            "操作时间": datetime.now(),
            "操作数量": quantity,
        }
        records = pd.DataFrame([new_record], columns=RECORD_COLUMNS) if records.empty else pd.concat([records, pd.DataFrame([new_record])], ignore_index=True)
        self._save_all(courses, records, enrollments, stopped)
        return f"选课成功：{course['课程名称']}（{course_id}）× {quantity}"

    def drop(self, student_id: str, course_id: str, quantity: int = 1):
        student_id = _normalize_student_id(student_id)
        course_id = _normalize_course_id(course_id)
        quantity = int(quantity)

        if not student_id:
            raise ValueError("学号不能为空。")
        if quantity <= 0:
            raise ValueError("退课数量必须为正整数。")

        courses, records, enrollments, stopped = self._load_all()
        idx = courses.index[courses["课程编号"].str.upper() == course_id].tolist()
        if not idx:
            raise ValueError(f"课程 {course_id} 不存在或已停开，不能从当前课程表执行退课。")

        mask = (
            enrollments["学号"].astype(str).eq(student_id)
            & enrollments["课程编号"].astype(str).str.upper().eq(course_id)
        )
        if not mask.any():
            raise ValueError(f"学生 {student_id} 当前没有选修课程 {course_id}。")

        j = enrollments.index[mask][0]
        held = int(enrollments.at[j, "数量"])
        if quantity > held:
            raise ValueError(f"退课失败：该学生当前仅有 {held} 个选课数量，不能退 {quantity}。")

        i = idx[0]
        selected = int(courses.at[i, "已选人数"])
        if selected < quantity:
            raise ValueError("数据异常：课程已选人数不足，无法继续扣减。")

        course = courses.loc[i]
        courses.at[i, "已选人数"] = selected - quantity

        remaining = held - quantity
        if remaining == 0:
            enrollments = enrollments.drop(index=j).reset_index(drop=True)
        else:
            enrollments.at[j, "数量"] = remaining

        new_record = {
            "课程编号": course["课程编号"],
            "课程名称": course["课程名称"],
            "课程类别": course["课程类别"],
            "开课学院": course["开课学院"],
            "操作类型": "退课",
            "操作人": student_id,
            "操作时间": datetime.now(),
            "操作数量": quantity,
        }
        records = pd.DataFrame([new_record], columns=RECORD_COLUMNS) if records.empty else pd.concat([records, pd.DataFrame([new_record])], ignore_index=True)
        self._save_all(courses, records, enrollments, stopped)
        return f"退课成功：{course['课程名称']}（{course_id}）× {quantity}"

    # -------------------- 课程停开 --------------------

    def stop_course(self, course_id: str):
        """
        从当前课程目录删除课程，但：
        1. records 历史日志完全保留；
        2. 课程信息放入 stopped_courses 归档；
        3. 当前 enrollments 中该课程状态删除（课程已不再开设）。
        """
        course_id = _normalize_course_id(course_id)
        courses, records, enrollments, stopped = self._load_all()

        idx = courses.index[courses["课程编号"].str.upper() == course_id].tolist()
        if not idx:
            raise ValueError(f"未找到课程 {course_id}。")

        i = idx[0]
        course = courses.loc[i]
        stopped_row = {col: course[col] for col in COURSE_COLUMNS}
        stopped_row["停开时间"] = datetime.now()
        stopped = pd.DataFrame([stopped_row], columns=STOPPED_COLUMNS) if stopped.empty else pd.concat([stopped, pd.DataFrame([stopped_row])], ignore_index=True)

        courses = courses.drop(index=i).reset_index(drop=True)
        enrollments = enrollments[
            ~enrollments["课程编号"].astype(str).str.upper().eq(course_id)
        ].reset_index(drop=True)

        self._save_all(courses, records, enrollments, stopped)
        return (
            f"课程已停开：{course['课程名称']}（{course_id}）。"
            f"历史选课/退课记录未删除。"
        )

    # -------------------- 记录查询 --------------------

    def query_records(
        self,
        course_id: Optional[str] = None,
        student_id: Optional[str] = None,
        start_time: Optional[str | datetime] = None,
        end_time: Optional[str | datetime] = None,
    ) -> pd.DataFrame:
        _, records, _, _ = self._load_all()
        result = records.copy()

        if result.empty:
            return result

        if course_id:
            cid = _normalize_course_id(course_id)
            result = result[result["课程编号"].astype(str).str.upper().eq(cid)]

        if student_id:
            sid = _normalize_student_id(student_id)
            result = result[result["操作人"].astype(str).eq(sid)]

        if start_time:
            start = pd.to_datetime(start_time)
            result = result[result["操作时间"] >= start]

        if end_time:
            end = pd.to_datetime(end_time)
            # 若用户只输入日期，例如 2026-09-16，则包含当天
            if isinstance(end_time, str) and len(end_time.strip()) <= 10:
                end = end + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
            result = result[result["操作时间"] <= end]

        return result.sort_values("操作时间", ascending=False).reset_index(drop=True)

    @staticmethod
    def week_to_range(semester_start: str, week_no: int) -> DateRange:
        start = pd.to_datetime(semester_start).normalize() + pd.Timedelta(days=(week_no - 1) * 7)
        end = start + pd.Timedelta(days=7) - pd.Timedelta(microseconds=1)
        return DateRange(start=start, end=end)

    # -------------------- 选课人次汇总 --------------------

    def summarize_enrollment(
        self,
        start_time: Optional[str | datetime] = None,
        end_time: Optional[str | datetime] = None,
        category: Optional[str] = None,
        group_by: Optional[str] = None,
    ):
        """
        只统计“选课”记录，不扣除退课。
        这符合“总选课人次 = 选课次数之和，不含退课”的题目定义。
        group_by: None / "课程" / "学院"
        """
        _, records, _, _ = self._load_all()
        if records.empty:
            if group_by:
                return pd.DataFrame(columns=[group_by, "选课人次"])
            return 0

        data = records[records["操作类型"].eq("选课")].copy()

        if start_time:
            data = data[data["操作时间"] >= pd.to_datetime(start_time)]

        if end_time:
            end = pd.to_datetime(end_time)
            if isinstance(end_time, str) and len(end_time.strip()) <= 10:
                end = end + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
            data = data[data["操作时间"] <= end]

        if category:
            data = data[data["课程类别"].astype(str).eq(category)]

        if group_by is None:
            return int(data["操作数量"].sum())

        if group_by == "课程":
            if data.empty:
                return pd.DataFrame(columns=["课程编号", "课程名称", "选课人次"])
            out = (
                data.groupby(["课程编号", "课程名称"], as_index=False)["操作数量"]
                .sum()
                .rename(columns={"操作数量": "选课人次"})
                .sort_values(["选课人次", "课程编号"], ascending=[False, True])
            )
            return out.reset_index(drop=True)

        if group_by == "学院":
            if data.empty:
                return pd.DataFrame(columns=["开课学院", "选课人次"])
            out = (
                data.groupby("开课学院", as_index=False)["操作数量"]
                .sum()
                .rename(columns={"操作数量": "选课人次"})
                .sort_values("选课人次", ascending=False)
            )
            return out.reset_index(drop=True)

        raise ValueError("group_by 只能为 None、'课程' 或 '学院'。")

    # -------------------- 其他辅助 --------------------

    def current_enrollments(self, student_id: Optional[str] = None) -> pd.DataFrame:
        _, _, enrollments, _ = self._load_all()
        result = enrollments.copy()
        if student_id:
            result = result[result["学号"].astype(str).eq(_normalize_student_id(student_id))]
        return result.reset_index(drop=True)


def print_df(df: pd.DataFrame):
    if df.empty:
        print("\n（无数据）\n")
        return
    print()
    print(df.to_string(index=False))
    print()


def input_int(prompt: str, default: int = 1) -> int:
    text = input(prompt).strip()
    if not text:
        return default
    return int(text)


def ask_date_range():
    print("时间筛选方式：")
    print("1. 直接输入起止日期")
    print("2. 按“学期开始日期 + 第几周”")
    print("3. 不限制时间")
    choice = input("请选择：").strip()

    if choice == "1":
        start = input("开始日期（YYYY-MM-DD，留空不限）：").strip() or None
        end = input("结束日期（YYYY-MM-DD，留空不限）：").strip() or None
        return start, end

    if choice == "2":
        semester_start = input("学期第一周周一日期（YYYY-MM-DD）：").strip()
        week_no = int(input("第几周：").strip())
        r = CourseSelectionSystem.week_to_range(semester_start, week_no)
        print(f"已换算为：{r.start} ~ {r.end}")
        return r.start, r.end

    return None, None


def show_catalog(system: CourseSelectionSystem):
    df = system.list_courses()
    if df.empty:
        print("\n当前没有开设课程。\n")
        return

    print("\n========== 课程目录 ==========")
    for category, group in df.groupby("课程类别", sort=False):
        print(f"\n【{category}】")
        print(group.to_string(index=False))
    print()


def main():
    system = CourseSelectionSystem()

    while True:
        print("=" * 58)
        print("          校园课程选课管理系统（文件系统版）")
        print("=" * 58)
        print("1. 查看课程目录")
        print("2. 选课")
        print("3. 退课")
        print("4. 课程停开")
        print("5. 查询选课/退课记录")
        print("6. 选课人次汇总")
        print("7. 查看某学生当前选课")
        print("0. 退出")
        choice = input("请选择功能：").strip()

        try:
            if choice == "1":
                show_catalog(system)

            elif choice == "2":
                sid = input("学号：").strip()
                cid = input("课程编号：").strip()
                qty = input_int("选课数量（默认1）：", 1)
                print(system.enroll(sid, cid, qty))

            elif choice == "3":
                sid = input("学号：").strip()
                cid = input("课程编号：").strip()
                qty = input_int("退课数量（默认1，可批量）：", 1)
                print(system.drop(sid, cid, qty))

            elif choice == "4":
                cid = input("要停开的课程编号：").strip()
                confirm = input(f"确认停开 {cid}？输入 YES 继续：").strip()
                if confirm == "YES":
                    print(system.stop_course(cid))
                else:
                    print("已取消。")

            elif choice == "5":
                print("\n可同时组合条件；不需要的条件直接回车。")
                cid = input("课程编号（可空）：").strip() or None
                sid = input("学号（可空）：").strip() or None
                start, end = ask_date_range()
                result = system.query_records(cid, sid, start, end)
                print_df(result)

            elif choice == "6":
                start, end = ask_date_range()
                category = input(
                    "课程类别（可空，如 公共必修/专业核心/专业选修/通识选修/体育专项）："
                ).strip() or None
                print("统计方式：1=总人次  2=按课程  3=按学院")
                mode = input("请选择：").strip()
                if mode == "2":
                    result = system.summarize_enrollment(start, end, category, "课程")
                    print_df(result)
                elif mode == "3":
                    result = system.summarize_enrollment(start, end, category, "学院")
                    print_df(result)
                else:
                    total = system.summarize_enrollment(start, end, category, None)
                    print(f"\n总选课人次：{total}\n")

            elif choice == "7":
                sid = input("学号（留空查看全部当前选课）：").strip() or None
                print_df(system.current_enrollments(sid))

            elif choice == "0":
                print("程序已退出。")
                break

            else:
                print("无效选项，请重新输入。")

        except Exception as e:
            print(f"\n操作失败：{e}\n")


if __name__ == "__main__":
    main()
