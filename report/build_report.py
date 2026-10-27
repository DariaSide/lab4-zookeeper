from __future__ import annotations

import shutil
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "report" / "Lab4_Apache_ZooKeeper.pdf"
USER_OUTPUT = Path("/Users/side/Documents/Codex/2026-10-21/hdfs-xa0-x43e-mapreduce-rustfs-json/outputs/Lab4_Apache_ZooKeeper.pdf")
REPOSITORY = "https://github.com/DariaSide/lab4-zookeeper"
UNFENCED = "unfenced-20261027T105157Z"
FENCED = "fenced-20261027T105312Z"
DIGEST = "ed6333305917179aa98d99c3040edb3673b8c6f97cbc597fce4dc97e58862a99"

font_candidates = [
    Path("/Users/side/Documents/Codex/2026-10-21/hdfs-xa0-x43e-mapreduce-rustfs-json/.venv/lib/python3.9/site-packages/matplotlib/mpl-data/fonts/ttf"),
    Path("/Users/side/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/lib/python3.11/site-packages/matplotlib/mpl-data/fonts/ttf"),
]
font_dir = next(path for path in font_candidates if (path / "DejaVuSans.ttf").exists())
pdfmetrics.registerFont(TTFont("DejaVu", str(font_dir / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(font_dir / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuMono", str(font_dir / "DejaVuSansMono.ttf")))

NAVY = colors.HexColor("#173B57")
TEAL = colors.HexColor("#168A8A")
LIGHT = colors.HexColor("#DCECF3")
INK = colors.HexColor("#1D2730")
MUTED = colors.HexColor("#5C6973")
DARK = colors.HexColor("#14232E")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleRU", fontName="DejaVu-Bold", fontSize=25, leading=31, textColor=NAVY, spaceAfter=12))
styles.add(ParagraphStyle(name="SubRU", fontName="DejaVu", fontSize=11, leading=16, textColor=MUTED, spaceAfter=7))
styles.add(ParagraphStyle(name="H1RU", fontName="DejaVu-Bold", fontSize=17, leading=22, textColor=NAVY, spaceBefore=6, spaceAfter=10))
styles.add(ParagraphStyle(name="H2RU", fontName="DejaVu-Bold", fontSize=12, leading=16, textColor=TEAL, spaceBefore=7, spaceAfter=6))
styles.add(ParagraphStyle(name="BodyRU", fontName="DejaVu", fontSize=9.3, leading=13.8, textColor=INK, spaceAfter=7))
styles.add(ParagraphStyle(name="SmallRU", fontName="DejaVu", fontSize=7.5, leading=10.5, textColor=INK))
styles.add(ParagraphStyle(name="MonoRU", fontName="DejaVuMono", fontSize=7.1, leading=10.0, textColor=colors.HexColor("#E8EEF2"), backColor=DARK, borderPadding=8, spaceAfter=8))
styles.add(ParagraphStyle(name="Callout", fontName="DejaVu-Bold", fontSize=10, leading=14, textColor=NAVY, backColor=LIGHT, borderPadding=9, spaceAfter=10))


def p(text: str, style: str = "BodyRU") -> Paragraph:
    return Paragraph(text, styles[style])


def code(text: str) -> Paragraph:
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
    return p(safe, "MonoRU")


def table(rows, widths):
    rendered = [[p(str(cell), "SmallRU") for cell in row] for row in rows]
    result = Table(rendered, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "DejaVu"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F9FA")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#B8C6CF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return result


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D5DEE4"))
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    canvas.setFont("DejaVu", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 9 * mm, "Лабораторная работа 4 - Apache ZooKeeper")
    canvas.drawRightString(192 * mm, 9 * mm, f"Страница {doc.page}")
    canvas.restoreState()


doc = BaseDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=17 * mm, bottomMargin=18 * mm,
                      title="Лабораторная работа 4. Apache ZooKeeper",
                      author="Дарья Сидельникова")
doc.addPageTemplates(PageTemplate(id="main", frames=Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height), onPage=footer))
story = []

story += [
    Spacer(1, 16 * mm), p("Лабораторная работа 4", "TitleRU"),
    p("Отказоустойчивость с Apache ZooKeeper", "TitleRU"), Spacer(1, 7 * mm),
    p("Координатор расчёта пар навыков DevOps", "Callout"),
    p("Студент: Сидельникова Дарья Николаевна<br/>Группа: ИИИ-3-ИнжДан-1-2<br/>Преподаватель: Артём Галимьянов<br/>Дата выполнения: 27 октября 2026 года", "SubRU"),
    Spacer(1, 5 * mm), p(f'<b>Репозиторий:</b> <link href="{REPOSITORY}" color="#168A8A">{REPOSITORY}</link>'),
    Spacer(1, 15 * mm), p("Цель", "H2RU"),
    p("Развернуть ансамбль ZooKeeper из трёх серверов, проверить кворум и эфемерные узлы, затем обеспечить автоматическую смену лидера для двух копий координатора. Отдельно показать опасность устаревшего лидера и защитить публикацию результата монотонной эпохой."),
]

story += [PageBreak(), p("1. Исходные данные и архитектура", "H1RU"),
          p("Расчёт продолжает ДЗ №3 для варианта «DevOps-инженер». Входом служит реальный экспорт 22 286 уникальных пар навыков. Обе копии координатора читают один и тот же NDJSON и проверяют его контрольную сумму."),
          table([["Контрольный показатель", "Значение"], ["Вакансий", "5 158"], ["Уникальных навыков", "1 560"], ["Уникальных пар", "22 286"], ["Уникальных троек", "152 375"], ["SHA-256 пар", DIGEST[:32] + "<br/>" + DIGEST[32:]]], [55 * mm, 107 * mm]),
          Spacer(1, 5 * mm), p("Компоненты", "H2RU"),
          table([["Компонент", "Назначение"], ["zk1, zk2, zk3", "ZooKeeper 3.9.6, отдельные myid, data и datalog"], ["coordinator-a", "Первая копия расчёта"], ["coordinator-b", "Резервная копия расчёта"], ["Election recipe", "Эфемерные последовательные узлы и выбор одного лидера"], ["Получатель результата", "Проверка эпохи и обновление указателя результата"]], [47 * mm, 115 * mm]),
          Spacer(1, 5 * mm),
          p("Координаторы подключаются к zk1:2181, zk2:2181 и zk3:2181 с тайм-аутом сессии 10 секунд. Расчёт разбит на 120 work units. После каждой части лидер сохраняет номер следующего блока в /skill-pairs/checkpoint. Поэтому резервная копия не начинает всё заново.")]

story += [PageBreak(), p("2. Настройка ансамбля", "H1RU"),
          p("Все три контейнера получают одинаковый список участников server.N, но разные ZOO_MY_ID. Клиентские порты на хосте: 2181, 2182 и 2183. Для каждого сервера созданы отдельные volumes /data и /datalog, чтобы журналы и снимки состояния не пересекались."),
          code("image: zookeeper:3.9.6\nZOO_TICK_TIME: 2000\nZOO_INIT_LIMIT: 5\nZOO_SYNC_LIMIT: 2\nZOO_SERVERS:\n  server.1=zk1:2888:3888;2181\n  server.2=zk2:2888:3888;2181\n  server.3=zk3:2888:3888;2181"),
          p("Роли серверов", "H2RU"),
          code("$ make status\nzk1: follower\nzk2: leader\nzk3: follower"),
          p("Лидер выбирается автоматически. Его номер не зафиксирован в compose-файле: после перезапуска лидером может стать другой участник. Для клиента это прозрачно, потому что он получает список всех трёх адресов.")]

story += [PageBreak(), p("3. Проверка кворума", "H1RU"),
          p("Сначала был остановлен один follower. Два оставшихся сервера сохранили большинство 2 из 3, поэтому тестовая запись прошла. Затем был остановлен второй сервер. Единственный оставшийся узел работал как процесс, но не мог подтвердить запись без большинства."),
          code("Initial roles\nzk1: follower\nzk2: leader\nzk3: follower\n\nStop one follower: zk1\nPASS: quorum still serves requests with two of three nodes\n\nStop second node: zk3\nPASS: one remaining node cannot commit a write\n\nRestored roles\nzk1: follower\nzk2: follower\nzk3: leader"),
          p("Результат", "Callout"),
          p("Потеря одного сервера не останавливает ансамбль. Потеря двух серверов оставляет 1 из 3, кворума нет, поэтому операции записи недоступны. После возврата серверов ансамбль самостоятельно выбрал лидера и снова начал обслуживать запросы.")]

story += [PageBreak(), p("4. Эфемерный узел", "H1RU"),
          p("Клиент создал /ephemeral-demo-88220 с флагом ephemeral. Пока сессия была открыта, команда get вернула значение alive. После закрытия клиента ZooKeeper удалил узел автоматически."),
          code("$ make ephemeral-test\nCreating ephemeral node /ephemeral-demo-88220\nCreated /ephemeral-demo-88220\nalive\n\n# новое подключение после закрытия первой сессии\nNode does not exist: /ephemeral-demo-88220\nPASS: ephemeral node disappeared when the client session closed"),
          p("Эфемерный узел связан не с процессом на сервере, а с клиентской сессией. Такой узел удобно использовать для регистрации живых экземпляров и выбора лидера: если координатор исчезает или перестаёт поддерживать сессию, его узел удаляется без отдельной команды очистки.")]

story += [PageBreak(), p("5. Failover без защиты по эпохе", "H1RU"),
          p(f"Прогон {UNFENCED} выполнен с FENCING=0. Первым лидером стал coordinator-a. Через три секунды контейнер был приостановлен командой SIGSTOP. Сессия перестала обновляться, и coordinator-b стал лидером через <b>10,800 с</b>."),
          code("coordinator-a became leader epoch=1\ncoordinator-a resumed from checkpoint next_unit=0/120\nPausing coordinator-a with SIGSTOP\n\ncoordinator-b became leader epoch=2\ncoordinator-b resumed from checkpoint next_unit=15/120\nBackup became leader after 10.800s"),
          p("Запасной координатор продолжил с блока 15/120 и записал 22 286 пар. После этого старый лидер был возобновлён и тоже записал результат. В обоих сообщениях SHA-256 совпал, но указатель результата обновился дважды."),
          code("coordinator-b wrote result epoch=2 pointer_version=1 unique_pairs=22286\ncoordinator-a wrote result epoch=1 pointer_version=2 unique_pairs=22286\n\nstat /skill-pairs/result\ndataVersion = 2"),
          p("Без fencing устаревший лидер не понимает, что право на запись уже передано другой копии. В этой демонстрации данные одинаковые, но в реальном приложении поздняя запись могла бы вернуть старое состояние.", "Callout")]

story += [PageBreak(), p("6. Failover с защитой по эпохе", "H1RU"),
          p(f"Прогон {FENCED} повторяет тот же сценарий с FENCING=1. Coordinator-b получил эпоху 2 и стал лидером через <b>10,338 с</b>. Он восстановился с checkpoint 15/120 и опубликовал результат."),
          code("coordinator-a became leader epoch=1\nPausing coordinator-a with SIGSTOP\n\ncoordinator-b became leader epoch=2\ncoordinator-b resumed from checkpoint next_unit=15/120\ncoordinator-b wrote result epoch=2 pointer_version=1 unique_pairs=22286"),
          p("После SIGCONT coordinator-a попытался опубликовать результат с эпохой 1. Получатель уже знал текущую эпоху 2 и отклонил запрос."),
          code("coordinator-a BadVersionError stale result rejected\nresult_epoch=1 current_epoch=2\n\nstat /skill-pairs/result\ndataVersion = 1"),
          p("В истории осталась одна принятая публикация. Указатель принадлежит запасному координатору, а его версия равна 1. Контрольная сумма результата совпала с ДЗ №3.", "Callout")]

story += [PageBreak(), p("7. Сравнение двух сценариев", "H1RU"),
          table([["Показатель", "Без fencing", "С fencing"], ["Время смены лидера", "10,800 с", "10,338 с"], ["Checkpoint нового лидера", "15/120", "15/120"], ["Принятых публикаций", "2", "1"], ["Версия указателя", "2", "1"], ["Устаревшая запись", "Принята", "Отклонена"], ["Контрольное число", "22 286", "22 286"], ["SHA-256", DIGEST[:20] + "...", DIGEST[:20] + "..."]], [56 * mm, 53 * mm, 53 * mm]),
          Spacer(1, 6 * mm),
          p("Проверка make verify", "H2RU"),
          code("PASS: unfenced run has two writes and pointer dataVersion 2\nPASS: fenced run has one write, stale write rejection, and 22,286 pairs"),
          p("Время failover немного больше 10 секунд, потому что к тайм-ауту сессии добавляются сетевой цикл клиента, удаление эфемерного election-узла и выполнение callback нового лидера.")]

story += [PageBreak(), p("8. Ответы на вопросы", "H1RU"),
          p("Почему три сервера, а не два и не четыре?", "H2RU"),
          p("ZooKeeper подтверждает запись большинством. У трёх серверов большинство равно двум, поэтому один сервер можно потерять. У двух серверов тоже нужны оба: после отказа одного останется 1 из 2, а этого недостаточно. Четыре сервера требуют кворум 3 из 4 и всё равно переживают только один отказ, то есть четвёртый сервер добавляет расходы, но не повышает допустимое число отказов. Чтобы пережить два отказа, нужны пять серверов и кворум из трёх."),
          p("Почему эпоху проверяет получатель записи?", "H2RU"),
          p("ZooKeeper может выдать новому лидеру больший номер эпохи, но он не управляет внешним файлом, объектом S3 или строкой базы данных. При паузе старый координатор может не узнать, что его сессия уже истекла, и продолжить начатую операцию. Поэтому номер эпохи передаётся вместе с результатом, а сервис, который действительно меняет данные, сравнивает его с последним принятым номером. Только получатель может гарантировать, что устаревшая запись не изменит состояние.")]

story += [PageBreak(), p("9. Итоги", "H1RU"),
          p("В работе поднят ансамбль ZooKeeper 3.9.6 из трёх серверов. Проверены роли, работа при потере одного сервера, остановка записей при потере двух серверов и автоматическое удаление эфемерного узла."),
          p("Две копии координатора обработали реальные 22 286 пар навыков из ДЗ №3. При остановке лидера запасная копия получила лидерство примерно за 10,5 секунды, прочитала checkpoint 15/120 и завершила расчёт с той же контрольной суммой."),
          p("Опыт без fencing показал две принятые публикации и версию указателя 2. После включения проверки эпохи поздняя запись старого лидера получила BadVersionError, а результат запасного координатора остался единственным."),
          p("Команды воспроизведения", "H2RU"),
          code("$ cp .env.example .env\n$ make build ensemble\n$ make status\n$ make quorum-test\n$ make ephemeral-test\n$ make demo-unfenced\n$ make demo-fenced\n$ make verify")]

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
USER_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
doc.build(story)
shutil.copy2(OUTPUT, USER_OUTPUT)
print(OUTPUT)
print(USER_OUTPUT)
