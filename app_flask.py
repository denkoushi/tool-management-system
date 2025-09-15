#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
互換ラッパー: 既存のエントリポイントを維持しつつ、新しい構成へ委譲します。

将来的には `python -m app.main` へ移行してください。
"""

from app.main import run


if __name__ == "__main__":
    run()
