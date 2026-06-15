import os
from pathlib import Path

import duckdb
import flet as ft


DB_FILE = "athlete_record.duckdb"
IMAGE_DIR = "images"


def prepare_images():
    """이미지 폴더와 임시 이미지 파일을 준비한다."""
    Path(IMAGE_DIR).mkdir(exist_ok=True)

    # 실제 이미지가 없을 경우에도 프로그램이 실행되도록 기본 파일 경로만 준비
    # 보고서 제출 전에는 images 폴더에 son.jpg, ahn.jpg 파일을 직접 넣으면 된다.
    return {
        "son": f"{IMAGE_DIR}/son.jpg",
        "ahn": f"{IMAGE_DIR}/ahn.png",
    }


def init_database():
    """DuckDB 데이터베이스를 생성하고 테이블 및 예시 데이터를 삽입한다."""
    image_paths = prepare_images()

    con = duckdb.connect(DB_FILE)

    con.execute("""
        CREATE TABLE IF NOT EXISTS track_event (
            event_id INTEGER PRIMARY KEY,
            event_name VARCHAR NOT NULL UNIQUE,
            event_type VARCHAR NOT NULL,
            unit VARCHAR NOT NULL
        );
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS athlete (
            athlete_id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            gender VARCHAR NOT NULL,
            school VARCHAR,
            birth_year INTEGER,
            main_event_id INTEGER NOT NULL,
            image_path VARCHAR,
            FOREIGN KEY (main_event_id)
                REFERENCES track_event(event_id)
        );
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS competition (
            competition_id INTEGER PRIMARY KEY,
            competition_name VARCHAR NOT NULL,
            competition_date DATE NOT NULL,
            location VARCHAR
        );
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS race_record (
            record_id INTEGER PRIMARY KEY,
            record_value DOUBLE NOT NULL,
            ranking INTEGER,
            memo VARCHAR,
            athlete_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            competition_id INTEGER NOT NULL,
            FOREIGN KEY (athlete_id)
                REFERENCES athlete(athlete_id),
            FOREIGN KEY (event_id)
                REFERENCES track_event(event_id),
            FOREIGN KEY (competition_id)
                REFERENCES competition(competition_id)
        );
    """)

    # 중복 삽입 방지를 위해 기존 예시 데이터 삭제 후 다시 삽입
    con.execute("DELETE FROM race_record;")
    con.execute("DELETE FROM athlete;")
    con.execute("DELETE FROM competition;")
    con.execute("DELETE FROM track_event;")

    con.execute("""
        INSERT INTO track_event VALUES
        (1, '100m', '트랙', '초'),
        (2, '200m', '트랙', '초');
    """)

    con.execute("""
        INSERT INTO athlete VALUES
        (?, '손정연', '남', '익산어양중학교', 2003, 1, ?),
        (?, '안성우', '남', '익산어양중학교', 2002, 2, ?);
    """, [1, image_paths["son"], 2, image_paths["ahn"]])

    con.execute("""
        INSERT INTO competition VALUES
        (1, '제18회 전국꿈나무선수선발육상경기대회', '2016-06-11', '광주월드컵경기장'),
        (2, '제46회 전국소년체육대회', '2017-05-28', '아산종합운동장');
    """)

    con.execute("""
        INSERT INTO race_record VALUES
        (1, 12.21, 1, '100m 경기 기록', 1, 1, 1),
        (2, 22.64, 1, '200m 경기 기록', 2, 2, 2);
    """)

    con.close()


def fetch_athletes():
    """선수 목록 조회"""
    con = duckdb.connect(DB_FILE)
    rows = con.execute("""
        SELECT
            a.athlete_id,
            a.name,
            a.gender,
            a.school,
            a.birth_year,
            te.event_name,
            a.image_path
        FROM athlete a
        LEFT JOIN track_event te
            ON a.main_event_id = te.event_id
        ORDER BY a.athlete_id;
    """).fetchall()
    con.close()
    return rows


def fetch_join_records():
    """세 개 이상의 테이블을 LEFT JOIN하여 통합 기록 조회"""
    con = duckdb.connect(DB_FILE)
    rows = con.execute("""
        SELECT
            a.name AS athlete_name,
            te.event_name,
            c.competition_name,
            c.competition_date,
            c.location,
            r.record_value,
            te.unit,
            r.ranking,
            r.memo
        FROM race_record r
        LEFT JOIN athlete a
            ON r.athlete_id = a.athlete_id
        LEFT JOIN track_event te
            ON r.event_id = te.event_id
        LEFT JOIN competition c
            ON r.competition_id = c.competition_id
        ORDER BY c.competition_date DESC;
    """).fetchall()
    con.close()
    return rows


def build_athlete_table():
    rows = fetch_athletes()

    return ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("선수ID")),
            ft.DataColumn(ft.Text("이름")),
            ft.DataColumn(ft.Text("성별")),
            ft.DataColumn(ft.Text("소속")),
            ft.DataColumn(ft.Text("출생연도")),
            ft.DataColumn(ft.Text("주종목")),
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(row[0]))),
                    ft.DataCell(ft.Text(row[1])),
                    ft.DataCell(ft.Text(row[2])),
                    ft.DataCell(ft.Text(row[3])),
                    ft.DataCell(ft.Text(str(row[4]))),
                    ft.DataCell(ft.Text(row[5])),
                ]
            )
            for row in rows
        ],
    )


def build_join_table():
    rows = fetch_join_records()

    return ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("선수명")),
            ft.DataColumn(ft.Text("종목")),
            ft.DataColumn(ft.Text("대회명")),
            ft.DataColumn(ft.Text("날짜")),
            ft.DataColumn(ft.Text("장소")),
            ft.DataColumn(ft.Text("기록")),
            ft.DataColumn(ft.Text("단위")),
            ft.DataColumn(ft.Text("순위")),
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(row[0])),
                    ft.DataCell(ft.Text(row[1])),
                    ft.DataCell(ft.Text(row[2])),
                    ft.DataCell(ft.Text(str(row[3]))),
                    ft.DataCell(ft.Text(row[4])),
                    ft.DataCell(ft.Text(str(row[5]))),
                    ft.DataCell(ft.Text(row[6])),
                    ft.DataCell(ft.Text(str(row[7]))),
                ]
            )
            for row in rows
        ],
    )


def build_image_section():
    athletes = fetch_athletes()
    image_controls = []

    for athlete in athletes:
        name = athlete[1]
        event_name = athlete[5]
        image_path = athlete[6]

        if os.path.exists(image_path):
            image = ft.Image(
                src=image_path,
                width=120,
                height=120,
                border_radius=10,
            )
        else:
            image = ft.Container(
                width=120,
                height=120,
                bgcolor=ft.Colors.GREY_300,
                border_radius=10,
                alignment=ft.Alignment(0, 0),
                content=ft.Text("이미지\n없음", text_align=ft.TextAlign.CENTER),
            )

        image_controls.append(
            ft.Container(
                width=180,
                padding=10,
                border_radius=10,
                content=ft.Column(
                    [
                        image,
                        ft.Text(name, size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(f"주종목: {event_name}"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )

    return ft.Row(image_controls, spacing=20, wrap=True)


def main(page: ft.Page):
    page.title = "육상 경기 기록 관리 시스템"
    page.scroll = ft.ScrollMode.AUTO
    page.window_width = 1200
    page.window_height = 800

    init_database()

    title = ft.Text(
        "육상 경기 기록 관리 시스템",
        size=28,
        weight=ft.FontWeight.BOLD,
    )

    description = ft.Text(
        "Flet과 DuckDB를 사용하여 선수, 종목, 대회, 경기 기록을 관리하는 데이터베이스 애플리케이션",
        size=14,
    )

    page.add(
        ft.Column(
            [
                title,
                description,
                ft.Divider(),

                ft.Text("1. 선수 이미지 출력", size=22, weight=ft.FontWeight.BOLD),
                build_image_section(),

                ft.Divider(),

                ft.Text("2. 선수 목록 조회", size=22, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [build_athlete_table()],
                    scroll=ft.ScrollMode.AUTO,
                ),

                ft.Divider(),

                ft.Text("3. LEFT JOIN 통합 기록 조회", size=22, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "race_record 테이블을 기준으로 athlete, track_event, competition 테이블을 LEFT JOIN한 결과",
                    size=13,
                ),
                ft.Row(
                    [build_join_table()],
                    scroll=ft.ScrollMode.AUTO,
                ),
            ],
            spacing=15,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)