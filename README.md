# Securing Agentic AI Systems  
### Threat Modeling and Defense Evaluation

## Team Members

- Brennen Meixner
- Jesus Mariano
- Alejandra Salazar

## Project Overview

Agentic AI systems combine large language models with tools, memory, APIs, and multi-step decision-making. These systems can do more than generate text; they can access information, execute functions, use external tools, and communicate with other agents.

These capabilities also introduce new cybersecurity risks. Malicious or untrusted instructions may influence an agent, cause tool misuse, expose stored information, or affect how agents communicate and make decisions.

This project will develop a limited multi-agent AI system and evaluate its security against selected attack methods. After identifying weaknesses, we will implement safeguards and retest the system to determine whether the protections reduce successful attacks without preventing the agents from completing their intended tasks.

## Problem Statement

As agentic AI systems become more widely used, their ability to interact with tools, memory, and external resources creates additional attack surfaces.

Traditional security controls may not fully address attacks that target how AI agents interpret instructions and make decisions. This project will examine security risks in a controlled multi-agent system and evaluate defensive controls designed to reduce those risks.

## Project Goals and Objectives

The main goals of the project are to:

- Define the components, assets, trust boundaries, and risks of the system.
- Build a repeatable multi-agent AI prototype.
- Test selected attack scenarios against the system.
- Identify security weaknesses within the agent workflow.
- Implement safeguards around tools, memory, inputs, outputs, and agent actions.
- Retest the system after the safeguards are added.
- Compare security results before and after the defenses are implemented.
- Evaluate whether security improvements affect normal agent functionality.

## Proposed Features and System Components

The proposed system may include:

- Multiple AI agents with separate responsibilities
- Local large language model
- Agent orchestration
- Controlled tools and APIs
- File access
- Test database access
- Memory components
- Logging of agent actions and tool requests
- Input and output validation
- Tool permission controls
- Memory restrictions
- Controlled security testing environment

The team may adjust the exact components as the project develops and is evaluated.

## Planned Technologies and Tools

- **Python** — primary programming language
- **LangChain** — agent orchestration and multi-agent workflow development
- **Ollama** — running large language models locally
- **GitHub** — version control, project organization, and documentation
- **Local development environment** — controlled environment for development and security testing

We may add additional tools as the project progresses.

## Initial Implementation Plan and Timeline

### Weeks 1–2: Research and Scope

- Review research related to agentic AI security.
- Define the system architecture and scope.
- Identify assets, trust boundaries, and selected attack scenarios.
- Finalize the initial threat model.

### Weeks 3–4: Prototype and Baseline

- Build the initial multi-agent system.
- Configure the selected tools, data, and memory components.
- Establish logging and repeatable test conditions.
- Perform baseline security testing.

### Week 5: Defense Implementation

- Add selected safeguards.
- Implement tool permission controls.
- Add input, output, and memory protections.

### Weeks 6–7: Evaluation

- Repeat the selected attack scenarios.
- Record security and task-performance results.
- Compare baseline and defended results.
- Identify which safeguards were effective.

### Week 8: Analysis and Delivery

- Analyze final results.
- Document findings and limitations.
- Complete project documentation.
- Prepare the final report and demonstration.

## Expected Outcome

The project is expected to produce a documented threat model, a reproducible multi-agent prototype, controlled security test cases, implemented safeguards, and a comparison of baseline and defended results.

The final evaluation will identify which safeguards improved security, whether legitimate tasks were affected, and where additional testing or security controls may be needed.

## Project Status

**Current Phase:** Project planning and research

We will add source code and implementation materials as the project progresses.
