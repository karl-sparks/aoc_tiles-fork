import re
from collections import defaultdict
from pathlib import Path
from pprint import pprint
from typing import List, Dict, Optional

import git
from git import GitCommandError
from loguru import logger

from aoc_tiles.colors import extension_to_colors
from aoc_tiles.config import Config


class SolutionFinder:
    def __init__(self, config: Config):
        self.config = config
        self.repository = git.Repo(config.aoc_dir)

        if self.config.session_cookie_path.exists():
            msg = f"This is a security risk!" \
                  f" Ensure that the {self.config.session_cookie_path} "
            if self.git_is_file_tracked(self.config.session_cookie_path):
                msg += "file is not tracked by git!"
                exit(f"[ERROR] Session cookie file is tracked by git. {msg} Aborting!")
            elif not self.git_is_file_ignored(self.config.session_cookie_path):
                msg += " is in your .gitignore!"
                print(f"[WARNING] Session cookie file is not git ignored. {msg}")

    def get_solution_paths_by_year(self, aoc_dir: Path) -> Dict[Optional[int], Dict[int, List[Path]]]:
        day_to_solution_paths = defaultdict(lambda: defaultdict(list))
        year_pattern = re.compile(self.config.year_pattern)
        day_pattern = re.compile(self.config.day_pattern)
        candidate_paths = sorted(self._find_recursive_solution_files(aoc_dir))
        logger.debug("Candidate paths: {}", candidate_paths)
        for path in candidate_paths:
            years = year_pattern.findall(str(path))
            days = day_pattern.findall(str(path))
            if not years:
                years.append(None)
            for year in years:
                if days:
                    day_to_solution_paths[year][int(days[0])].append(path)

        self._ensure_sorting(day_to_solution_paths)
        # pprint(day_to_solution_paths)
        return day_to_solution_paths

    def _ensure_sorting(self, solution_paths_dict: Dict[int, Dict[int, List[str]]]) -> Dict[int, Dict[int, List[str]]]:
        def sort_key(path: Path):
            suffix = path.suffix.lower()
            if suffix in self.config.language_sorting:
                return self.config.language_sorting.index(suffix), suffix
            return 99999, suffix

        for year in solution_paths_dict:
            for day in solution_paths_dict[year]:
                solution_paths_dict[year][day] = sorted(solution_paths_dict[year][day], key=sort_key)
        return solution_paths_dict

    def _find_recursive_solution_files(self, directory: Path) -> List[Path]:
        solution_paths = []
        for path in directory.rglob("*"):
            # Either we don't care about git ignores, or we care and then check if file is ignored
            not_git_ignored = not self.config.only_use_solutions_in_git
            not_git_ignored |= self.config.only_use_solutions_in_git and self.git_is_file_tracked(path)
            if path.is_file() and path.suffix in extension_to_colors() and not_git_ignored:
                solution_paths.append(path)
        return solution_paths

    def git_is_file_ignored(self, filepath):
        try:
            self.repository.git.execute(['git', 'check-ignore', '-q', str(filepath)])
            return True
        except GitCommandError:
            return False

    def git_get_tracked_files(self) -> List[str]:
        return self.repository.git.ls_files().split('\n')

    def git_is_file_tracked(self, filepath: Path):
        tracked_files = self.git_get_tracked_files()
        return str(filepath) in tracked_files

    def git_add(self, path: Path):
        if path.exists():
            self.repository.git.add(str(path))


def main():
    SolutionFinder(Config()).get_solution_paths_by_year(Path())


if __name__ == "__main__":
    main()
