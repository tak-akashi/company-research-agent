"""IRテンプレート管理コマンド."""

from __future__ import annotations

import argparse
import logging

from company_research_agent.cli.output import (
    print_error,
    print_info,
    print_success,
    print_warning,
)

logger = logging.getLogger(__name__)


async def cmd_ir_template(args: argparse.Namespace) -> int:
    """IRテンプレート管理コマンドを実行.

    Args:
        args: コマンドライン引数

    Returns:
        終了コード (0: 成功, 1: エラー)
    """
    if args.action == "create":
        return await _create_template(args)
    elif args.action == "list":
        return await _list_templates(args)
    elif args.action == "validate":
        return await _validate_template(args)
    else:
        print_error("不明なアクションです: create, list, validate のいずれかを指定してください")
        return 1


async def _create_template(args: argparse.Namespace) -> int:
    """テンプレートを作成する.

    Args:
        args: コマンドライン引数

    Returns:
        終了コード
    """
    from rich.console import Console

    from company_research_agent.clients.ir_scraper.base import BaseIRScraper
    from company_research_agent.clients.ir_scraper.template_generator import (
        IRTemplateGenerator,
    )

    console = Console()

    # 必須引数チェック
    if not args.sec_code:
        print_error("--sec-code を指定してください")
        return 1

    # 企業名の取得
    company_name = args.company_name
    edinet_code = args.edinet_code

    if not company_name:
        # EDINETコードリストから企業名を取得を試みる
        try:
            from company_research_agent.clients.edinet_code_list_client import (
                EDINETCodeListClient,
            )

            client = EDINETCodeListClient()
            company = await client.get_by_sec_code(args.sec_code)
            if company:
                company_name = company.company_name
                if not edinet_code:
                    edinet_code = company.edinet_code
                print_info(f"企業名を取得しました: {company_name}")
            else:
                print_error("--company-name を指定してください（企業名を自動取得できませんでした）")
                return 1
        except Exception as e:
            print_error(f"企業名の自動取得に失敗しました: {e}")
            print_error("--company-name を指定してください")
            return 1

    # IR URLの取得（指定がない場合はWeb検索）
    ir_url = args.ir_url
    generator = IRTemplateGenerator()

    if not ir_url:
        print_info(f"IRページをWeb検索中: {company_name}")
        ir_url = await generator.discover_ir_url(
            company_name=company_name,
            sec_code=args.sec_code,
        )
        if not ir_url:
            print_error("IRページが見つかりませんでした。--ir-url で直接指定してください。")
            return 1
        print_success(f"IRページを発見: {ir_url}")

    print_info(f"テンプレートを生成中: {company_name} ({args.sec_code})")
    print_info(f"  IR URL: {ir_url}")

    try:
        async with BaseIRScraper() as scraper:
            # テンプレート生成
            template = await generator.generate_template(
                scraper=scraper,
                sec_code=args.sec_code,
                company_name=company_name,
                ir_url=ir_url,
                edinet_code=edinet_code,
            )

            # 結果を表示
            console.print("\n[bold]生成されたテンプレート:[/bold]")
            console.print(f"  企業名: {template.company.name}")
            console.print(f"  証券コード: {template.company.sec_code}")
            console.print(f"  ベースURL: {template.ir_page.base_url}")
            console.print(f"  セクション数: {len(template.ir_page.sections)}")

            for cat, section in template.ir_page.sections.items():
                console.print(f"\n  [cyan]{cat}[/cyan]:")
                console.print(f"    URL: {section.url}")
                console.print(f"    セレクター: {section.selector}")
                if section.link_pattern:
                    console.print(f"    リンクパターン: {section.link_pattern}")

            # 検証
            if not args.skip_validation:
                print_info("\nテンプレートを検証中...")
                validation_results = await generator.validate_template(scraper, template)

                has_error = False
                for cat, count in validation_results.items():
                    if count < 0:
                        console.print(f"  [red]{cat}: エラー[/red]")
                        has_error = True
                    elif count == 0:
                        console.print(f"  [yellow]{cat}: 0件[/yellow]")
                    else:
                        console.print(f"  [green]{cat}: {count}件のPDFを検出[/green]")

                if has_error:
                    print_warning(
                        "検証でエラーが発生しました。テンプレートの調整が必要かもしれません。"
                    )

            # 保存
            if args.save:
                try:
                    filepath = generator.save_template(template, overwrite=args.force)
                    print_success(f"テンプレートを保存しました: {filepath}")
                except FileExistsError as e:
                    print_error(f"{e}")
                    print_info("上書きするには --force オプションを使用してください")
                    return 1
            else:
                print_info("\nテンプレートを保存するには --save オプションを使用してください")

        return 0

    except Exception as e:
        logger.exception("テンプレート生成中にエラーが発生しました")
        print_error(f"エラー: {e}")
        return 1


async def _list_templates(args: argparse.Namespace) -> int:
    """登録済みテンプレート一覧を表示する.

    Args:
        args: コマンドライン引数

    Returns:
        終了コード
    """
    from rich.console import Console
    from rich.table import Table

    from company_research_agent.clients.ir_scraper.template_loader import TemplateLoader

    console = Console()
    loader = TemplateLoader()

    sec_codes = loader.list_templates()

    if not sec_codes:
        print_warning("登録済みテンプレートがありません")
        return 0

    table = Table(title="IRテンプレート一覧")
    table.add_column("証券コード", style="cyan")
    table.add_column("企業名", style="green")
    table.add_column("セクション", style="yellow")

    for sec_code in sec_codes:
        template = loader.load_template(sec_code)
        if template:
            sections = ", ".join(template.ir_page.sections.keys())
            table.add_row(sec_code, template.company.name, sections)

    console.print(table)
    print_info(f"合計: {len(sec_codes)}件")

    return 0


async def _validate_template(args: argparse.Namespace) -> int:
    """テンプレートを検証する.

    Args:
        args: コマンドライン引数

    Returns:
        終了コード
    """
    from rich.console import Console

    from company_research_agent.clients.ir_scraper.base import BaseIRScraper
    from company_research_agent.clients.ir_scraper.template_generator import (
        IRTemplateGenerator,
    )
    from company_research_agent.clients.ir_scraper.template_loader import TemplateLoader

    console = Console()

    if not args.sec_code:
        print_error("--sec-code を指定してください")
        return 1

    loader = TemplateLoader()
    template = loader.load_template(args.sec_code)

    if not template:
        print_error(f"テンプレートが見つかりません: {args.sec_code}")
        return 1

    print_info(f"テンプレートを検証中: {template.company.name} ({args.sec_code})")

    try:
        generator = IRTemplateGenerator()

        async with BaseIRScraper() as scraper:
            validation_results = await generator.validate_template(scraper, template)

            has_error = False
            total_docs = 0

            for cat, count in validation_results.items():
                if count < 0:
                    console.print(f"  [red]{cat}: エラー[/red]")
                    has_error = True
                elif count == 0:
                    console.print(f"  [yellow]{cat}: 0件[/yellow]")
                else:
                    console.print(f"  [green]{cat}: {count}件のPDFを検出[/green]")
                    total_docs += count

            if has_error:
                print_warning("検証でエラーが発生しました")
                return 1
            elif total_docs == 0:
                print_warning("PDFが検出されませんでした。テンプレートの調整が必要かもしれません。")
                return 1
            else:
                print_success(f"検証成功: 合計{total_docs}件のPDFを検出")
                return 0

    except Exception as e:
        logger.exception("検証中にエラーが発生しました")
        print_error(f"エラー: {e}")
        return 1
