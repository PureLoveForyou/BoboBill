import csv
import io
from openpyxl import load_workbook
from .base import build_col_map, find_csv_header, find_excel_header, parse_csv_rows, parse_excel_rows

_HEADER_CHECK = lambda line: '交易时间' in line and ('交易分类' in line or '交易对方' in line)
_HEADER_CHECK_EXCEL = lambda vals: '交易时间' in str(vals) and ('交易分类' in str(vals) or '交易对方' in str(vals))


def parse_alipay_csv(content_str: str) -> list:
    lines = content_str.strip().split('\n')
    header_idx = find_csv_header(lines, _HEADER_CHECK)
    if header_idx == -1:
        raise ValueError("无法识别支付宝账单格式：找不到表头")

    delimiter = '\t' if '\t' in lines[header_idx] else ','
    reader = csv.reader(lines[header_idx:], delimiter=delimiter)
    headers = [h.strip() for h in next(reader)]
    return parse_csv_rows(reader, build_col_map(headers), 'alipay')


def parse_alipay_excel(content: bytes) -> list:
    wb = load_workbook(io.BytesIO(content))
    ws = wb.active
    header_idx, headers = find_excel_header(ws, _HEADER_CHECK_EXCEL)
    if header_idx is None:
        raise ValueError("无法识别支付宝账单格式：找不到表头")
    return parse_excel_rows(ws, header_idx, build_col_map(headers), 'alipay')
