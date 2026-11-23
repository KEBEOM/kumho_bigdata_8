"""엑셀과 CSV 읽기, 중복 머리글 검사, 결과 파일 내보내기."""
from io import BytesIO
from pathlib import Path
import numpy as np
import pandas as pd
from analysis import AnalysisError

MAX_BYTES = 10 * 1024 * 1024


def excel_sheets(raw, filename):
    _check_size(raw)
    try:
        with pd.ExcelFile(BytesIO(raw), engine='xlrd' if filename.lower().endswith('.xls') else 'openpyxl') as book:
            return book.sheet_names
    except Exception as exc:
        raise AnalysisError('엑셀 파일을 읽지 못했습니다. 암호나 손상 여부를 확인하고 .xlsx로 다시 저장해 주세요.') from exc


def _check_size(raw):
    if not raw:
        raise AnalysisError('빈 파일입니다. 데이터가 들어 있는 파일을 선택해 주세요.')
    if len(raw) > MAX_BYTES:
        raise AnalysisError('10MB 이하의 파일만 사용할 수 있습니다.')


def read_data(raw: bytes, filename: str, sheet_name=0):
    _check_size(raw)
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == '.csv':
            try:
                content = raw.decode('utf-8-sig')
            except UnicodeDecodeError:
                content = raw.decode('cp949')
            from io import StringIO
            full = pd.read_csv(StringIO(content), header=None, nrows=10002)
        elif suffix in ('.xlsx','.xls'):
            full = pd.read_excel(BytesIO(raw), sheet_name=sheet_name, header=None,
                                 engine='xlrd' if suffix=='.xls' else 'openpyxl', nrows=10002)
        else:
            raise AnalysisError('.xlsx, .xls, .csv 파일만 지원합니다.')
    except AnalysisError:
        raise
    except Exception as exc:
        raise AnalysisError('파일을 읽지 못했습니다. 첫 행은 열 이름, 둘째 행부터는 데이터가 되도록 저장해 주세요. CSV는 UTF-8 또는 CP949를 지원합니다.') from exc
    if len(full) < 2 or full.shape[1] == 0:
        raise AnalysisError('열 이름과 데이터가 필요합니다. 빈 시트가 아닌지 확인해 주세요.')
    if len(full)-1 > 10000 or full.shape[1] > 100:
        raise AnalysisError('이 앱은 최대 10,000행, 100열을 지원합니다. 필요한 자료만 남겨 주세요.')
    if full.iloc[0].isna().any():
        raise AnalysisError('이름이 비어 있는 열이 있습니다. 첫 행의 모든 열에 이름을 입력해 주세요.')
    header = [str(c).strip() for c in full.iloc[0]]
    if any(not c for c in header) or len(header) != len(set(header)):
        raise AnalysisError('열 이름이 비어 있거나 중복되었습니다. 첫 행의 이름을 고쳐 주세요.')
    df = full.iloc[1:].copy().reset_index(drop=True)
    df.columns = header
    with pd.option_context('future.no_silent_downcasting', True):
        df = df.replace(r'^\s*$', np.nan, regex=True)
    for c in df.columns:
        converted = pd.to_numeric(df[c], errors='coerce')
        if df[c].notna().sum() > 0 and converted.notna().sum() == df[c].notna().sum():
            df[c] = converted
    return df


def export_excel(tables: dict, summary: str) -> bytes:
    """외부 문자열은 수식이 아닌 문자로 저장한다."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        pd.DataFrame({'분석 안내': summary.splitlines()}).to_excel(writer, sheet_name='분석안내', index=False)
        for i, (name, table) in enumerate(tables.items(), 1):
            safe_name = ''.join(c for c in name if c not in '[]:*?/\\')[:25]
            table.to_excel(writer, sheet_name=f'{i}_{safe_name}', index=False)
        for sheet in writer.book:
            sheet.freeze_panes = 'A2'
            sheet.auto_filter.ref = sheet.dimensions
            for row in sheet.iter_rows():
                for cell in row:
                    if isinstance(cell.value, str):
                        cell.data_type = 's'
            for cells in sheet.columns:
                width = max(len(str(c.value or '')) for c in list(cells)[:60])
                sheet.column_dimensions[cells[0].column_letter].width = min(50,max(15,width*1.4))
    return buffer.getvalue()
