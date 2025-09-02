import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

try:
    from colorama import Fore, Style, init

    init(autoreset=True)
except ImportError:
    # Fallback if colorama not available
    class Fore:
        RED = "\033[0;31m"
        GREEN = "\033[0;32m"
        YELLOW = "\033[1;33m"
        BLUE = "\033[0;34m"
        CYAN = "\033[0;36m"
        RESET = "\033[0m"

    class Style:
        RESET_ALL = "\033[0m"


# Export for use by other modules
__all__ = ["CCHeavy", "Fore", "Style"]


class CCHeavy:
    """Cursor CLI Heavy Research System"""

    def __init__(self):
        self.max_assistants = 8
        self.parallel_agents = 4

        # Will be set during execution
        self.query = ""
        self.output_format = "markdown"
        self.working_dir = ""
        self.working_dir_abs = ""
        self.output_dir = ""
        self.output_dir_abs = ""
        self.ext = "md"
        # Dynamic focuses decided by orchestrator {assistant_index: focus}
        self.assistant_focuses = {}
        # Synthesis prompt provided by orchestrator
        self.synthesis_prompt = ""

    def generate_folder_name(self, query: str, max_length: int = 60) -> str:
        """Generate a folder-friendly name from a query"""
        # Convert to lowercase and replace special chars with spaces
        clean = re.sub(r"[^a-z0-9 ]", " ", query.lower())

        # Replace spaces with hyphens and remove multiple hyphens
        clean = re.sub(r" +", "-", clean)
        clean = re.sub(r"-+", "-", clean)
        clean = clean.strip("-")

        # Truncate if too long
        if len(clean) > max_length:
            clean = clean[:max_length]
            # Remove trailing partial word
            clean = re.sub(r"-[^-]*$", "", clean)

        return clean

    def get_focus_for_index(self, idx: int) -> str:
        """Get research focus area for assistant index"""
        focuses = {
            1: "Factual research and direct information",
            2: "Analysis and metrics",
            3: "Alternative perspectives and criticisms",
            4: "Case studies and examples",
            5: "Implementation challenges and risks",
            6: "Future trends and research gaps",
            7: "Ethical, legal, and societal implications",
            8: "Contrarian view and edge cases",
        }
        return focuses.get(idx, "General research")

    def print_banner(self):
        """Print the application banner"""
        print(f"{Fore.CYAN}")
        print("╔════════════════════════════════════════╗")
        print("║       Cursor CLI Heavy Research        ║")
        print("╚════════════════════════════════════════╝")
        print(f"{Style.RESET_ALL}")

    def interactive_mode(self) -> Tuple[str, str, str]:
        """Run interactive mode to collect user input"""

        # Get research question
        print(f"{Fore.GREEN}What would you like to research?{Style.RESET_ALL}")
        query = input("> ").strip()
        if not query:
            print(f"{Fore.RED}Query cannot be empty.{Style.RESET_ALL}")
            sys.exit(1)

        # Get output format
        print(
            f"\n{Fore.GREEN}Output format?{Style.RESET_ALL} (markdown/text, or press Enter for markdown)"
        )
        output_format = input("> ").strip() or "markdown"

        # Get working directory
        print(
            f"\n{Fore.GREEN}Working directory to analyze?{Style.RESET_ALL} (absolute path, or press Enter to skip)"
        )
        working_dir = input("> ").strip()

        # Confirm settings
        print(f"\n{Fore.BLUE}Ready to start research with:{Style.RESET_ALL}")
        print(f"  📝 Query: {query}")
        print(f"  📄 Format: {output_format}")
        print(f"  📂 Working Dir: {working_dir or '(none)'}")
        print("  👥 Agents: (decided by orchestrator)")

        print(f"\n{Fore.GREEN}Proceed? (Y/n){Style.RESET_ALL}")
        confirm = input("> ").strip().lower()

        if confirm and not confirm.startswith("y"):
            print(f"{Fore.YELLOW}Cancelled.{Style.RESET_ALL}")
            sys.exit(0)

        return query, output_format, working_dir

    def setup_directories(self):
        """Setup output directories"""
        folder_name = self.generate_folder_name(self.query)
        date = datetime.now().strftime("%Y-%m-%d")
        self.output_dir = f"./outputs/{date}-{folder_name}"

        # Create directories
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(f"{self.output_dir}/assistants").mkdir(exist_ok=True)

        # Get absolute path
        self.output_dir_abs = Path(self.output_dir).resolve()

        # Setup working directory
        if self.working_dir:
            working_path = Path(self.working_dir)
            if working_path.exists() and working_path.is_dir():
                self.working_dir_abs = str(working_path.resolve())
            else:
                print(
                    f"{Fore.YELLOW}Warning:{Style.RESET_ALL} Working directory '{self.working_dir}' not found. Falling back to temporary run directory."
                )
                self.working_dir = ""
                self.working_dir_abs = ""

        # Set file extension
        self.ext = "md" if self.output_format == "markdown" else "txt"

    def run_cursor_agent(
        self,
        prompt_content: str,
        output_file: str,
        error_file: Optional[str] = None,
        run_dir: Optional[str] = None,
    ) -> bool:
        """Run cursor-agent with given prompt and capture output"""
        try:
            # Determine run directory
            if run_dir is None:
                if self.working_dir_abs:
                    run_dir = self.working_dir_abs
                else:
                    run_dir = tempfile.mkdtemp()

            # Build command
            cmd = [
                "cursor-agent",
                "-p",
                prompt_content,
                "--model",
                "gpt-5",
                "--output-format",
                "text",
            ]

            # Run command
            with open(output_file, "w") as out_f:
                error_output = None
                if error_file:
                    error_output = open(error_file, "w")

                try:
                    result = subprocess.run(
                        cmd, cwd=run_dir, stdout=out_f, stderr=error_output, text=True
                    )
                    return result.returncode == 0
                finally:
                    if error_output:
                        error_output.close()

        except Exception as e:
            with open(output_file, "a") as f:
                f.write(f"\nError running cursor-agent: {e}")
            return False

    def run_parallel_research(self):
        """Run parallel research with multiple cursor-agent workers"""
        print(
            f"{Fore.YELLOW}Spawning {self.parallel_agents} cursor-agent workers...{Style.RESET_ALL}"
        )

        # Write research plan
        plan_file = self.output_dir_abs / f"research-plan.{self.ext}"
        with open(plan_file, "w") as f:
            f.write("# Research Plan\n\n")
            f.write(f"**Query:** {self.query}\n\n")
            f.write(f"**Mode:** Parallel ({self.parallel_agents} assistants)\n\n")
            f.write("## Assistant Roles\n")
            for i in range(1, self.parallel_agents + 1):
                focus = self.assistant_focuses.get(i) or self.get_focus_for_index(i)
                f.write(f"- RA-{i}: {focus}\n")

        # Launch workers concurrently
        with ThreadPoolExecutor(max_workers=self.parallel_agents) as executor:
            futures = []

            for i in range(1, self.parallel_agents + 1):
                focus = self.assistant_focuses.get(i) or self.get_focus_for_index(i)

                # Create prompt content
                prompt_content = f"""You are Research Assistant RA-{i} working in parallel on the following query:

"{self.query}"

Your specific focus: {focus}

Instructions:
- Produce a focused, self-contained {self.output_format} report
- Cite credible sources using inline markdown links
- No meta commentary, no planning output, no placeholders
- Output only the final report content as {self.output_format}"""

                output_file = (
                    self.output_dir_abs / f"assistants/ra-{i}-findings.{self.ext}"
                )
                error_file = self.output_dir_abs / f"assistants/ra-{i}-stderr.log"

                # Determine and display run directory for this agent
                agent_run_dir = (
                    self.working_dir_abs
                    if self.working_dir_abs
                    else "temporary directory"
                )

                # Submit task
                future = executor.submit(
                    self._run_assistant_with_retry,
                    prompt_content,
                    str(output_file),
                    str(error_file),
                    i,
                )
                futures.append(future)

                print(
                    f"{Fore.GREEN}✓ Launched RA{i} ({focus}) from: {agent_run_dir}{Style.RESET_ALL}"
                )

            # Wait for completion
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"{Fore.RED}Assistant task failed: {e}{Style.RESET_ALL}")

        print(f"{Fore.CYAN}All assistants have completed.{Style.RESET_ALL}")

        # Synthesis step
        self._run_synthesis()

    def _run_assistant_with_retry(
        self, prompt_content: str, output_file: str, error_file: str, assistant_num: int
    ):
        """Run assistant with retry logic"""
        # Determine run directory for this assistant
        run_dir = None
        if self.working_dir_abs:
            run_dir = self.working_dir_abs
        else:
            # Create temp directory for this specific assistant if no working dir specified
            run_dir = tempfile.mkdtemp()

        # First attempt
        success = self.run_cursor_agent(
            prompt_content, output_file, error_file, run_dir
        )

        # Check if output is empty or whitespace only
        try:
            with open(output_file, "r") as f:
                content = f.read().strip()
            if not content:
                # Retry once
                time.sleep(1)
                success = self.run_cursor_agent(
                    prompt_content, output_file, error_file, run_dir
                )
        except FileNotFoundError:
            success = False

        if not success:
            with open(output_file, "a") as f:
                f.write(f"\nRA-{assistant_num}: cursor-agent failed. See {error_file}")

        # Clean up temp directory if we created one
        if not self.working_dir_abs and run_dir:
            try:
                shutil.rmtree(run_dir)
            except Exception:
                pass  # Ignore cleanup errors

    def _run_synthesis(self):
        """Run synthesis of all assistant reports"""
        synth_input = self.output_dir_abs / "synthesis-input.txt"

        with open(synth_input, "w") as f:
            if self.synthesis_prompt:
                f.write(self.synthesis_prompt + "\n\n")
            else:
                f.write(
                    f"You are a senior analyst. Synthesize the following assistant reports into a single comprehensive {self.output_format} analysis with an executive summary, key findings, areas of agreement/disagreement, and recommended next steps. Cite with inline markdown links.\n\n"
                )

            for i in range(1, self.parallel_agents + 1):
                f.write(f"\n===== BEGIN RA-{i} =====\n")

                findings_file = (
                    self.output_dir_abs / f"assistants/ra-{i}-findings.{self.ext}"
                )
                try:
                    with open(findings_file, "r") as rf:
                        f.write(rf.read())
                except FileNotFoundError:
                    f.write(f"RA-{i} output not found")

                f.write(f"\n===== END RA-{i} =====\n\n")

        # Run synthesis
        with open(synth_input, "r") as f:
            synth_prompt = f.read()

        final_output = self.output_dir_abs / f"final-analysis.{self.ext}"

        # Use specified working directory or create temp directory for synthesis
        synth_run_dir = (
            self.working_dir_abs if self.working_dir_abs else tempfile.mkdtemp()
        )
        self.run_cursor_agent(synth_prompt, str(final_output), run_dir=synth_run_dir)

        # Clean up temp directory if we created one
        if not self.working_dir_abs and synth_run_dir:
            try:
                shutil.rmtree(synth_run_dir)
            except Exception:
                pass  # Ignore cleanup errors

        print(
            f"{Fore.GREEN}Parallel research complete. Outputs saved under: {self.output_dir_abs}{Style.RESET_ALL}"
        )

    def create_orchestration_prompt(self):
        """Create the orchestration prompt file"""
        content = f"""# Cursor CLI Heavy - Research Orchestration

You are orchestrating a comprehensive parallel research system. You have full control over the research process.

## Research Query
**{self.query}**

## Output Directory
The wrapper will save files under: `{self.output_dir_abs}`.

## Important I/O Contract
- Do not write files or run commands. Print all outputs to stdout only.
- Use the exact block tags below so the wrapper can parse your outputs:
  - [BEGIN_PLAN] ... [END_PLAN]
  - [BEGIN_RA_1] ... [END_RA_1]
  - [BEGIN_RA_2] ... [END_RA_2]
  - ... up to RA_8 as needed
  - [BEGIN_FINAL] ... [END_FINAL]
  - [BEGIN_SYNTH_PROMPT] ... [END_SYNTH_PROMPT] (REQUIRED)
- All blocks should be valid markdown.

## Working Directory Context
If provided, you are being launched from: `{self.working_dir_abs}`.

- Do not modify any files in that directory.
- Do not run commands or write files. Print to stdout only.

## Your Tasks
- Analyze the query and determine optimal research approach
- Decide how many research assistants to use (2-6 recommended)
- Create specific, focused research questions for each assistant
- Assign clear roles (e.g., "Technology Expert", "Economic Analyst", etc.)
- Coordinate the research in parallel

## Research Process
1. Planning Phase
   - Analyze: "{self.query}"
   - Determine the number of assistants needed
   - Create research questions that cover all important angles
   - Print the plan inside [BEGIN_PLAN] ... [END_PLAN]

## Guidelines
- Use 2-8 assistants based on query complexity
- Each assistant should have a specific focus

Begin by analyzing the query and creating your research plan."""
        if self.output_format == "markdown":
            prompt_file = self.output_dir_abs / "orchestration-prompt.md"
        else:
            prompt_file = self.output_dir_abs / "orchestration-prompt.txt"

        with open(prompt_file, "w") as f:
            f.write(content)

        return prompt_file

    def extract_block(self, content: str, start_tag: str, end_tag: str) -> str:
        """Extract content between start and end tags"""
        pattern = f"{re.escape(start_tag)}(.*?){re.escape(end_tag)}"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def parse_session_output(self, session_file: Path):
        """Parse tagged sections from session log into separate files"""
        try:
            with open(session_file, "r") as f:
                content = f.read()
        except FileNotFoundError:
            return

        # Extract plan
        plan_content = self.extract_block(content, "[BEGIN_PLAN]", "[END_PLAN]")
        if plan_content:
            with open(self.output_dir_abs / f"research-plan.{self.ext}", "w") as f:
                f.write(plan_content)

        # Extract assistant findings
        for i in range(1, self.max_assistants + 1):
            ra_content = self.extract_block(content, f"[BEGIN_RA_{i}]", f"[END_RA_{i}]")
            if ra_content:
                (self.output_dir_abs / "assistants").mkdir(exist_ok=True)
                with open(
                    self.output_dir_abs / f"assistants/ra-{i}-findings.{self.ext}", "w"
                ) as f:
                    f.write(ra_content)

        # Extract final analysis
        final_content = self.extract_block(content, "[BEGIN_FINAL]", "[END_FINAL]")
        if final_content:
            with open(self.output_dir_abs / f"final-analysis.{self.ext}", "w") as f:
                f.write(final_content)

        # Extract JSON plan to set dynamic agents and focuses
        try:
            plan_json = self.extract_block(
                content, "[BEGIN_PLAN_JSON]", "[END_PLAN_JSON]"
            )
            if plan_json:
                data = json.loads(plan_json)
                count = int(data.get("assistant_count", 0))
                if 2 <= count <= self.max_assistants:
                    self.parallel_agents = count
                focuses = data.get("assistant_focuses") or {}
                parsed_focuses = {}
                if isinstance(focuses, dict):
                    for key, value in focuses.items():
                        try:
                            idx = int(key)
                        except (ValueError, TypeError):
                            continue
                        if not (1 <= idx <= self.max_assistants):
                            continue
                        if isinstance(value, str) and value.strip():
                            parsed_focuses[idx] = value.strip()
                elif isinstance(focuses, list):
                    for i, val in enumerate(focuses, start=1):
                        if i > self.max_assistants:
                            break
                        if isinstance(val, str) and val.strip():
                            parsed_focuses[i] = val.strip()
                if parsed_focuses:
                    self.assistant_focuses = parsed_focuses

            synth_prompt = self.extract_block(
                content, "[BEGIN_SYNTH_PROMPT]", "[END_SYNTH_PROMPT]"
            )
            if synth_prompt:
                self.synthesis_prompt = synth_prompt.strip()
        except Exception:
            # Silently ignore malformed JSON; fallback logic will apply
            pass

    def run_planning_orchestrator(self) -> None:
        """Run a lightweight planning orchestrator to decide count and focuses.

        The orchestrator must print a JSON block between [BEGIN_PLAN_JSON] and [END_PLAN_JSON]
        with the following structure:
        {
          "assistant_count": <int 2-8>,
          "assistant_focuses": {"1": "...", "2": "..."} or ["...", "..."]
        }
        """
        prompt = f"""
You are the Planning Orchestrator for a parallel research workflow.

Task:
- Analyze the user query below and decide how many research assistants are needed (between 2 and 8).
- For each assistant, assign a concise, specific focus area tailored to the query.

I/O Contract:
- Output only a single JSON object between the tags [BEGIN_PLAN_JSON] and [END_PLAN_JSON]. Also output a synthesis instruction block between [BEGIN_SYNTH_PROMPT] and [END_SYNTH_PROMPT] to be used as the synthesis prompt. The synthesis prompt is REQUIRED.
- Do not include any text outside the tagged blocks.
- The JSON must include keys "assistant_count" and "assistant_focuses".

Query: "{self.query}"

Constraints:
- assistant_count must be an integer between 2 and 8.
- assistant_focuses can be either an object mapping string indices ("1", "2", ...) to focus strings, or an array of focus strings in order.
- Focus examples: "Factual baseline and key definitions", "Market sizing and metrics", "Risks and failure modes", etc.

Now produce the JSON plan. After the JSON block, also print a tailored synthesis instruction block between [BEGIN_SYNTH_PROMPT] and [END_SYNTH_PROMPT].
"""

        # Use specified working directory or a temp directory
        run_dir = self.working_dir_abs if self.working_dir_abs else tempfile.mkdtemp()
        session_file = self.output_dir_abs / "planning-session.log"
        try:
            success = self.run_cursor_agent(prompt, str(session_file), run_dir=run_dir)
            if success:
                self.parse_session_output(session_file)
                if not self.synthesis_prompt:
                    print(
                        f"{Fore.YELLOW}Planning step did not provide a synthesis prompt. Retrying once...{Style.RESET_ALL}"
                    )
                    # Retry once
                    success_retry = self.run_cursor_agent(
                        prompt, str(session_file), run_dir=run_dir
                    )
                    if success_retry:
                        self.parse_session_output(session_file)
                if not self.synthesis_prompt:
                    raise RuntimeError(
                        "Planning orchestrator did not provide required synthesis prompt."
                    )
        finally:
            if not self.working_dir_abs and run_dir:
                try:
                    shutil.rmtree(run_dir)
                except Exception:
                    pass

    def _print_manual_instructions(self, prompt_file: Path):
        """Print manual run instructions"""
        print(f"\n{Fore.CYAN}══ Manual Run Instructions ══{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}To start:{Style.RESET_ALL}")

        if self.working_dir_abs:
            print(
                f'1. Run: {Fore.GREEN}cd "{self.working_dir_abs}" && cursor-agent -p "$(cat "{prompt_file}")" --model "gpt-5" --output-format text{Style.RESET_ALL}'
            )
        else:
            print(
                f'1. Run: {Fore.GREEN}cursor-agent -p "$(cat "{prompt_file}")" --model "gpt-5" --output-format text{Style.RESET_ALL}'
            )

        print("\n2. The agent will print outputs. Save the blocks to files under:")
        print(f"   {Fore.BLUE}{self.output_dir_abs}{Style.RESET_ALL}")

    def run(self, args):
        """Main execution method"""
        self.print_banner()

        if not args.query:
            # Interactive mode
            self.query, self.output_format, self.working_dir = self.interactive_mode()
        else:
            # Command line mode
            self.query = args.query
            self.output_format = args.format
            self.working_dir = args.workdir or ""

        # Setup
        self.setup_directories()

        print(f"{Fore.YELLOW}Query:{Style.RESET_ALL} {self.query}")
        print(f"{Fore.YELLOW}Output:{Style.RESET_ALL} {self.output_dir_abs}")
        print(
            f"{Fore.YELLOW}Working Dir:{Style.RESET_ALL} {self.working_dir_abs or '(none)'}"
        )

        print(
            f"\n{Fore.BLUE}Proceed to run orchestrator and assistants? (Y/n){Style.RESET_ALL}"
        )

        if not args.no_prompt:
            launch = input("> ").strip().lower()
            if launch and not launch.startswith("y"):
                prompt_file = self.create_orchestration_prompt()
                self._print_manual_instructions(prompt_file)
                return

        # Check if cursor-agent is available
        try:
            subprocess.run(["cursor-agent", "--help"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(
                f"{Fore.RED}cursor-agent command not found. Please ensure Cursor CLI is installed.{Style.RESET_ALL}"
            )
            print(
                f"{Fore.YELLOW}Install: {Fore.GREEN}curl https://cursor.com/install -fsS | bash{Style.RESET_ALL}"
            )
            return

        # Run planning orchestrator to decide count and focuses
        print(f"{Fore.YELLOW}Planning assistant configuration...{Style.RESET_ALL}")
        self.run_planning_orchestrator()

        # Fallbacks if orchestrator did not set values
        if not (2 <= self.parallel_agents <= self.max_assistants):
            self.parallel_agents = 4
        if not self.assistant_focuses:
            # Seed with defaults up to decided count
            self.assistant_focuses = {
                i: self.get_focus_for_index(i)
                for i in range(1, self.parallel_agents + 1)
            }

        # Run research
        self.run_parallel_research()

        # Final message
        print(
            f"{Fore.YELLOW}All outputs saved to: {self.output_dir_abs}{Style.RESET_ALL}"
        )
