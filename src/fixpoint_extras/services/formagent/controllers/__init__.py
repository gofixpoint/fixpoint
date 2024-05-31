"""
A controller can be thought of a controller (duh) or a manager of other AI
agents and the process for how they work together to accomplish something. It's
a higher level way to compose and coordiante agents.

In some cases, there can be overlap of responsibility between "agents" and
"controllers", but we think of the difference like this:

Agents are backed by some AI, and they can take multiple steps, but generally
you just ask the agent to accomplish something and it does it.

Controllers can layer on top of a single agent, or can coordinate multiple
agents, and expose interfaces designed to be controlled by our software systems
or other AIs. They are meta-agents that coordinate or modify the behavior of
other agent(s) and let those agents easily integrate with other software
systems.

In general, controllers do not have a uniform interface between controllers.

It looks like this "AI controller" nomenclature is being explored in other
places:

https://www.microsoft.com/en-us/research/blog/ai-controller-interface-generative-ai-with-a-lightweight-llm-integrated-vm/
"""
