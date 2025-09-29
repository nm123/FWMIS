"""
Test Runner Worker Module

Contains the TestRunnerWorker class for executing test suites in a separate thread.
"""

import subprocess
import time
import os
from typing import Dict, List, Optional

from PyQt5.QtCore import QThread, pyqtSignal


class TestRunnerWorker(QThread):
    """
    Worker thread for running test suites.

    Signals:
        progress_updated: Emitted when test progress updates (str)
        test_completed: Emitted when test execution completes (dict)
        output_updated: Emitted for each line of test output (str)
    """

    progress_updated = pyqtSignal(str)
    test_completed = pyqtSignal(dict)
    output_updated = pyqtSignal(str)

    def __init__(self, test_command: List[str], working_dir: str, env_vars: Optional[Dict[str, str]] = None):
        """
        Initialize the test runner worker.

        Args:
            test_command: List of command arguments to execute
            working_dir: Working directory for test execution
            env_vars: Optional environment variables to set for the test process
        """
        super().__init__()
        self.test_command = test_command
        self.working_dir = working_dir
        self.env_vars = env_vars or {}
        self.start_time = time.time()

    def run(self) -> None:
        """
        Execute the test suite in a separate thread.
        """
        try:
            self.progress_updated.emit("Starting test execution...")

            # Run the test command with environment variables
            env = os.environ.copy()
            env.update(self.env_vars)

            process = subprocess.Popen(
                self.test_command,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env,
            )

            output_lines = []
            line_count = 0
            buffered_output = []
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    output_lines.append(line)
                    line_count += 1
                    buffered_output.append(line)

                    # Only emit output updates for important lines and buffer others
                    if any(keyword in line.lower() for keyword in ['passed', 'failed', 'error', 'session starts', 'session ends']):
                        # Flush buffer before important messages
                        if buffered_output:
                            self.output_updated.emit("... (output buffered for performance)")
                            buffered_output = []
                        self.output_updated.emit(line)

                    # Update progress very infrequently
                    if line_count % 50 == 0:
                        self.progress_updated.emit(
                            f"Running tests... ({line_count} lines processed)"
                        )

            return_code = process.poll()

            # Parse results
            results: Dict = {
                "return_code": return_code,
                "success": return_code == 0,
                "output": "\n".join(output_lines),
                "duration": time.time() - self.start_time,
            }

            self.test_completed.emit(results)

        except Exception as e:
            self.test_completed.emit(
                {
                    "return_code": -1,
                    "success": False,
                    "output": f"Error running tests: {e}",
                    "duration": 0,
                }
            )
