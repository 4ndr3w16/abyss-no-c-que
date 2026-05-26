#!/usr/bin/env python3
# ============================================================
# main.py — Entry point. Run: python main.py
# ============================================================
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))

from core.game import Game


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
