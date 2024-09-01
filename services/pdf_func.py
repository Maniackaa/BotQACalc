import datetime
from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Mm, Inches

from config.bot_settings import settings, logger, BASE_DIR
from database.db import get_price, get_count


def format_new_doc(data):
    doc = Document()
    # Изменяем поля документа
    section = doc.sections[0]

    # Устанавливаем поля (в дюймах)
    doc.sections[0].page_width = Mm(210)
    section.top_margin = Mm(5)    # Верхнее поле
    section.bottom_margin = Mm(5)  # Нижнее поле
    section.left_margin = Mm(5)    # Левое поле
    section.right_margin = Mm(5)   # Правое поле
    # doc = doc('шаблон расчета.docx')
    img_path = BASE_DIR / 'header.png'
    doc.add_picture(img_path.as_posix(), width=Mm(200))
    styles = doc.styles
    for style in styles:
        if style.type == style.type.TABLE:
            print(style.name)

    for paragraph in doc.paragraphs:
        if '{date}' in paragraph.text:
            print(paragraph.text)
            paragraph.text = paragraph.text.replace("{date}", "new_value")

    p = doc.add_paragraph().add_run(text=f'Дата: {datetime.datetime.now(tz=settings.tz).date()}')
    p.bold = True
    p = doc.add_paragraph().add_run(text=f'Телефон клиента: {data["1"]}')
    p.bold = True
    doc.add_paragraph()
    p = doc.add_paragraph().add_run(text=f'Марка автомобиля: {data["2"]}')
    p.bold = True

    header = ('Комплектация',	'Характеристики', 'Цвет',	'',	'Стоимость',	'Кол-во',	'Итого')
    # for style in styles:
    #     if style.type == style.type.TABLE and style.name not in ['Normal Table']:
    # doc.add_paragraph().add_run(style.name)
    total_price = 0
    table_price = 0
    table = doc.add_table(rows=len(data['step1']) + 1, cols=7)
    # table.style = style.name
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    # Заголовок таблицы
    for i, cell in enumerate(hdr_cells):
        hdr_cells[i].text = header[i]
        cell_font = cell.paragraphs[0].runs[0]
        cell_font.bold = True
        # cell._element.get_or_add_tcPr().append(parse_xml(r'<w:shd {} w:fill="A9A9A9"/>'.format(nsdecls('w'))))

    # Заполнение строк таблицы
    logger.debug(f'steps1: {data["step1"]}')
    for row_num, step1 in enumerate(data['step1'], 1):
        logger.debug(f'Ряд {row_num}, {step1}')
        price = step1[4]
        count = step1[3]  # Введите количество комплектов
        total = round(float(price) * float(count))
        table_price += total
        logger.debug(f'price: {price}, count: {count}, total: {total}')
        row = [step1[0], step1[1], step1[2], step1[5], price, count, total]
        logger.debug(f'row: {row}')
        cells = table.rows[row_num].cells
        for i, cell in enumerate(cells):
            cell.text = str(row[i])
    total_price += table_price

    doc.add_paragraph()

    # Итого
    table = doc.add_table(rows=1, cols=3)
    table_price = 0
    table.style = 'Table Grid'
    table.autofit = False
    page_width = int(doc.sections[0].page_width.mm) - int(doc.sections[0].left_margin.mm) - int(doc.sections[0].right_margin.mm) + 3

    row_cells = table.rows[0].cells
    for i in range(3):
        cell = row_cells[i]
        cell._element.get_or_add_tcPr().append(parse_xml(r'<w:shd {} w:fill="00FF00"/>'.format(nsdecls('w'))))

    cell_to_merge = table.cell(0, 0)
    cell_to_merge.merge(table.cell(0, 1))
    cell_to_merge.text = 'ИТОГО'
    cell = table.cell(0, 2)
    cell.text = f'{total_price}'

    discount = True
    if discount:
        table.add_row()
        row_cells = table.rows[1].cells
        for i in range(1, 3):
            cell = row_cells[i]
            cell._element.get_or_add_tcPr().append(parse_xml(r'<w:shd {} w:fill="00CA00"/>'.format(nsdecls('w'))))
        cell = table.cell(1, 1)
        cell.text = f'ИТОГО с учетом %'

    # Устанавливаем ширину для последнего столбца

    last_cell_width = 30
    cell_width = int((page_width - last_cell_width) / 2)
    x = 30
    widths = (Mm(cell_width + x), Mm(cell_width - x), Mm(last_cell_width))
    for row in table.rows:
        for idx, width in enumerate(widths):
            row.cells[idx].width = width
    table.add_row()
    table._tbl.remove(table.rows[1]._tr)
    table._tbl.remove(table.rows[1]._tr)
    # doc.add_picture('photo.jpg', width=Inches(6.25))
    # doc.add_page_break()

    doc.save('demo.docx')
    return doc


if __name__ == '__main__':
    data = {'count': 8, 'step1': [['Комплект ковриков', 'Platinum 10мм', 'Серый', '1', '20000', ''], ['Комплект ковриков', 'Platinum 10мм', 'Серый', '1', '20000', '']], 'q_content_type': 'text', '1': '09049ш0294', '2': 'Chrysler', '3': 'Комплект ковриков', '4': 'Platinum 10мм', '5': 'Серый', '6': '1', '7': '20000', '8': 'Нет', '9': 'Нет'}
    format_new_doc(data)


