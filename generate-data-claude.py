# -*- coding: utf-8 -*-
"""
Mock Data Generator - Policy Renewal (SCK Insurance)
ตาม Spec v5.2.1

อ่าน Input CSV -> สร้าง Output CSV ที่มีข้อมูลจำลอง (Mock Data)
ตามกฎเกณฑ์ที่ระบุใน spec_v5_2_1.md อย่างเคร่งครัด
"""

import random
from datetime import date, timedelta

import pandas as pd
from dateutil.relativedelta import relativedelta
from faker import Faker

# ---------------------------------------------------------------------------
# 2.1 Constants
# ---------------------------------------------------------------------------
RENEWAL_DATE = date(2026, 9, 12)

THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]

INPUT_PATH = "SCK-insurance.csv"
OUTPUT_PATH = "SCK-insurance-mockdata.csv"

fake_th = Faker("th_TH")
fake_en = Faker("en_US")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def to_be_year(d: date) -> int:
    """แปลง ปี ค.ศ. -> พ.ศ."""
    return d.year + 543


def thai_date_str(d: date) -> str:
    """[วัน] [เดือนภาษาไทย] [ปี พ.ศ.]"""
    return f"{d.day} {THAI_MONTHS[d.month]} {to_be_year(d)}"


def random_date_between(start: date, end: date) -> date:
    """สุ่มวันที่ระหว่าง start และ end (inclusive) อย่างปลอดภัยแม้ start > end"""
    if start > end:
        start, end = end, start
    delta_days = (end - start).days
    if delta_days <= 0:
        return start
    offset = random.randint(0, delta_days)
    return start + timedelta(days=offset)


def age_years_days(birth_date: date, as_of: date) -> tuple[int, int]:
    """คำนวณอายุ (ปี, วัน) ตามปฏิทินจริงโดยใช้ relativedelta"""
    rd = relativedelta(as_of, birth_date)
    # หาวันเกิดล่าสุดที่ผ่านมา (ครบปีล่าสุด) เพื่อคำนวณจำนวนวันที่เหลือ
    last_birthday = birth_date + relativedelta(years=rd.years)
    days = (as_of - last_birthday).days
    return rd.years, days


def gen_thai_id() -> str:
    """สุ่มเลขบัตรประชาชน 13 หลัก พร้อมคำนวณ checksum (Modulo 11) ตามเกณฑ์กรมการปกครอง"""
    digits = [random.randint(0, 9) for _ in range(12)]
    total = sum(d * (13 - i) for i, d in enumerate(digits))
    check_digit = (11 - (total % 11)) % 10
    digits.append(check_digit)
    return "".join(str(d) for d in digits)


def gen_phone() -> str:
    return "08" + "".join(str(random.randint(0, 9)) for _ in range(8))


# ---------------------------------------------------------------------------
# 2.2 Timeline -> advance_days
# ---------------------------------------------------------------------------
def calc_advance_days(timeline: str) -> int:
    timeline = (timeline or "").strip()
    if timeline == "90 - 30 วันล่วงหน้า":
        return random.randint(30, 90)
    if timeline == "29 - 1 วันล่วงหน้า":
        return random.randint(1, 29)
    if timeline == "ภายในวันที่หมดอายุ":
        return 0
    raise ValueError(f"Unknown Timeline value: {timeline!r}")


# ---------------------------------------------------------------------------
# 2.4 Birthday ranges
# ---------------------------------------------------------------------------
def adult_normal_bday_range():
    min_bday = RENEWAL_DATE - relativedelta(years=60)
    max_bday = RENEWAL_DATE - relativedelta(years=40)
    return min_bday, max_bday


def adult_overage_bday_range(policy_start_date: date, expiry_date: date):
    min_bday = policy_start_date - relativedelta(years=65) + timedelta(days=1)
    max_bday = expiry_date - relativedelta(years=65)
    return min_bday, max_bday


def child_normal_bday_range():
    min_bday = RENEWAL_DATE - relativedelta(years=13)
    max_bday = RENEWAL_DATE - relativedelta(years=1)
    return min_bday, max_bday


def child_overage_bday_range(policy_start_date: date, expiry_date: date):
    min_bday = policy_start_date - relativedelta(years=15) + timedelta(days=1)
    max_bday = expiry_date - relativedelta(years=15)
    return min_bday, max_bday


# ---------------------------------------------------------------------------
# 4. Family mapping table (ทำตามตารางตรงๆ ห้ามตีความเอง)
#    tuple ค่า = (สถานะคู่สมรส, สถานะบุตรคนที่ 1, สถานะบุตรคนที่ 2)
#    สถานะที่เป็นไปได้: None, "ปกติ", "อายุเกิน", "เสียชีวิต"
# ---------------------------------------------------------------------------
FAMILY_MAP = {
    "คู่สมรสปกติ ไม่มีบุตร": ("ปกติ", None, None),
    "คู่สมรสปกติ บุตร 1 คน": ("ปกติ", "ปกติ", None),
    "คู่สมรสปกติ บุตร 2 คน": ("ปกติ", "ปกติ", "ปกติ"),
    "ไม่มีคู่สมรส บุตร 1 คน": (None, "ปกติ", None),
    "ไม่มีคู่สมรส บุตร 2 คน": (None, "ปกติ", "ปกติ"),
    "ไม่มีคู่สมรส บุตร 1 คนอายุเกิน": (None, "อายุเกิน", None),
    "ไม่มีคู่สมรส บุตร 2 คนอายุเกิน": (None, "อายุเกิน", "อายุเกิน"),
    "ไม่มีคู่สมรส บุตรเสียชีวิต 1 คน": (None, "เสียชีวิต", None),
    "ไม่มีคู่สมรส บุตรเสียชีวิต 2 คน": (None, "เสียชีวิต", "เสียชีวิต"),
    "คู่สมรสอายุเกิน บุตร 2 คน": ("อายุเกิน", "ปกติ", "ปกติ"),
    "คู่สมรสอายุเกิน บุตร 1 คนอายุเกิน": ("อายุเกิน", "อายุเกิน", None),
    "คู่สมรสอายุเกิน บุตร 2 คนอายุเกิน": ("อายุเกิน", "อายุเกิน", "อายุเกิน"),
    "คู่สมรสอายุเกิน บุตรเสียชีวิต 1 คน": ("อายุเกิน", "เสียชีวิต", None),
    "คู่สมรสอายุเกิน บุตรเสียชีวิต 2 คน": ("อายุเกิน", "เสียชีวิต", "เสียชีวิต"),
    "คู่สมรสเสียชีวิต บุตร 2 คน": ("เสียชีวิต", "ปกติ", "ปกติ"),
    "คู่สมรสเสียชีวิต บุตร 1 คนอายุเกิน": ("เสียชีวิต", "อายุเกิน", None),
    "คู่สมรสเสียชีวิต บุตร 2 คนอายุเกิน": ("เสียชีวิต", "อายุเกิน", "อายุเกิน"),
    "คู่สมรสเสียชีวิต บุตรเสียชีวิต 1 คน": ("เสียชีวิต", "เสียชีวิต", None),
    "คู่สมรสเสียชีวิต บุตรเสียชีวิต 2 คน": ("เสียชีวิต", "เสียชีวิต", "เสียชีวิต"),
}


# ---------------------------------------------------------------------------
# Person generation
# ---------------------------------------------------------------------------
def gen_person_name():
    first_th = fake_th.first_name()
    last_th = fake_th.last_name()
    first_en = fake_en.first_name()
    return first_th, last_th, first_en


def gen_policyholder(as_of: date) -> str:
    """ผู้ถือกรมธรรม์ - สุ่มอายุกรณีปกติเสมอ"""
    first_th, last_th, first_en = gen_person_name()
    min_bday, max_bday = adult_normal_bday_range()
    bday = random_date_between(min_bday, max_bday)
    years, days = age_years_days(bday, as_of)

    lines = [
        f"ชื่อ: {first_th} {last_th}",
        f"เลขบัตรประชาชน: {gen_thai_id()}",
        f"เบอร์โทรศัพท์: {gen_phone()}",
        f"อีเมล: {first_en.lower()}@email.com",
        f"ว/ด/ป เกิด: {thai_date_str(bday)}",
        f"อายุ: {years} ปี {days} วัน",
    ]
    return "\n".join(lines)


def gen_member_block(label: str, status: str, is_adult: bool,
                      policy_start_date: date, expiry_date: date,
                      renewal_date: date) -> str:
    """
    label: 'คู่สมรส' หรือ 'บุตรคนที่ N'
    status: 'ปกติ' | 'อายุเกิน' | 'เสียชีวิต'
    is_adult: True สำหรับคู่สมรส, False สำหรับบุตร

    หมายเหตุเรื่องวันอ้างอิงคำนวณอายุ (as_of):
    - กรณี 'ปกติ' ช่วงวันเกิดถูกกำหนดโดยอิง RENEWAL_DATE จึงรายงานอายุ ณ RENEWAL_DATE
    - กรณี 'อายุเกิน' นิยามคือ ผู้นั้นอายุครบเกณฑ์ (65/15 ปี) ณ วันสิ้นสุดความคุ้มครอง (expiry_date)
      จึงรายงานอายุ ณ expiry_date เพื่อให้สอดคล้องกับนิยามของกลุ่มนี้
    """
    if status == "เสียชีวิต":
        return f"{label}: เสียชีวิต"

    first_th, last_th, _ = gen_person_name()

    if is_adult:
        if status == "ปกติ":
            min_bday, max_bday = adult_normal_bday_range()
            as_of = renewal_date
        else:  # อายุเกิน
            min_bday, max_bday = adult_overage_bday_range(policy_start_date, expiry_date)
            as_of = expiry_date
    else:
        if status == "ปกติ":
            min_bday, max_bday = child_normal_bday_range()
            as_of = renewal_date
        else:  # อายุเกิน
            min_bday, max_bday = child_overage_bday_range(policy_start_date, expiry_date)
            as_of = expiry_date

    bday = random_date_between(min_bday, max_bday)
    years, days = age_years_days(bday, as_of)

    lines = [
        f"{label}: มีชีวิต ({status})" if status == "อายุเกิน" else f"{label}: มีชีวิต",
        f"ชื่อ: {first_th} {last_th}",
        f"ว/ด/ป เกิด: {thai_date_str(bday)}",
        f"อายุ: {years} ปี {days} วัน",
    ]
    return "\n".join(lines)


def gen_members_column(family_text: str, bundle: str,
                        policy_start_date: date, expiry_date: date,
                        as_of: date) -> str:
    bundle = (bundle or "").strip()
    family_text = (family_text or "").strip()

    if bundle == "SCK Personal" or family_text == "":
        return ""

    if "Family" not in bundle:
        return ""

    if family_text not in FAMILY_MAP:
        raise ValueError(f"Unknown Family value: {family_text!r}")

    spouse_status, child1_status, child2_status = FAMILY_MAP[family_text]

    blocks = []
    if spouse_status is not None:
        blocks.append(
            gen_member_block("คู่สมรส", spouse_status, True,
                              policy_start_date, expiry_date, as_of)
        )
    if child1_status is not None:
        blocks.append(
            gen_member_block("บุตรคนที่ 1", child1_status, False,
                              policy_start_date, expiry_date, as_of)
        )
    if child2_status is not None:
        blocks.append(
            gen_member_block("บุตรคนที่ 2", child2_status, False,
                              policy_start_date, expiry_date, as_of)
        )

    return "\n\n".join(blocks)


def gen_status_column(advance_days: int, expiry_date: date,
                       policy_start_date: date) -> str:
    lines = [
        f"จำนวนวันที่ต่ออายุล่วงหน้า: {advance_days} วัน",
        f"วันที่ต่ออายุ: {thai_date_str(RENEWAL_DATE)}",
        f"วันสิ้นสุดความคุ้มครอง: {thai_date_str(expiry_date)}",
        f"วันเริ่มสัญญาฉบับปัจจุบัน: {thai_date_str(policy_start_date)}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    df = pd.read_csv(INPUT_PATH)

    out_rows = []
    for _, row in df.iterrows():
        timeline = row["Timeline"]
        bundle = row["Bundle"]
        family = row["Family"] if pd.notna(row["Family"]) else ""

        advance_days = calc_advance_days(timeline)

        # 2.3 คำนวณวันที่ในสัญญา
        expiry_date = RENEWAL_DATE + timedelta(days=advance_days)
        policy_start_date = expiry_date - relativedelta(years=1)

        # ใช้ RENEWAL_DATE เป็นวันอ้างอิงคำนวณอายุผู้ถือกรมธรรม์ (กรณีปกติเสมอ)
        policyholder_col = gen_policyholder(RENEWAL_DATE)

        # สมาชิกในกรมธรรม์: อายุ ณ RENEWAL_DATE (กรณีปกติ) หรือ ณ expiry_date (กรณีอายุเกิน)
        # ใช้ RENEWAL_DATE เป็นวันอ้างอิงหลักในการรายงานอายุ ให้สอดคล้องกับผู้ถือกรมธรรม์
        members_col = gen_members_column(
            family, bundle, policy_start_date, expiry_date, RENEWAL_DATE
        )

        status_col = gen_status_column(advance_days, expiry_date, policy_start_date)

        out_rows.append({
            "Timeline": timeline,
            "Bundle": bundle,
            "Family": family,
            "ข้อมูลผู้ถือกรมธรรม์": policyholder_col,
            "ข้อมูลสมาชิกในกรมธรรม์": members_col,
            "Status": status_col,
        })

    out_df = pd.DataFrame(out_rows, columns=[
        "Timeline", "Bundle", "Family",
        "ข้อมูลผู้ถือกรมธรรม์", "ข้อมูลสมาชิกในกรมธรรม์", "Status",
    ])

    out_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"Wrote {len(out_df)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()