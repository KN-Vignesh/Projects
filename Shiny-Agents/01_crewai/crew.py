import os

from agent import MODEL, coder, list_files, read_file

from crewai import Agent, Crew, Task

from dotenv import load_dotenv

load_dotenv()  # the imported agent validates GEMINI_API_KEY

planner = Agent(
    role="Tech Lead",
    goal="Break the user's request into a short, concrete build plan.",
    backstory="A pragmatic tech lead who writes plans a junior dev can follow.",
    tools=[list_files, read_file],
    llm=MODEL,
    verbose=True,
)


def main():
    request = os.getenv("AGENT_REQUEST") or input("What should the crew build? ")

    plan_task = Task(
        description=f"Look at the files in this folder, then write a step by step plan for: {request}",
        expected_output="A numbered build plan, 5 steps or fewer.",
        agent=planner,
    )
    build_task = Task(
        description="Follow the plan exactly and build it.",
        expected_output="A short summary of what was built and which files changed.",
        agent=coder,
        context=[plan_task],  # the coder receives the planner's output
    )

    crew = Crew(agents=[planner, coder], tasks=[plan_task, build_task])
    result = crew.kickoff()
    print(f"\n{result}")


if __name__ == "__main__":
    main()
