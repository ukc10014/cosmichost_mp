# Introduction

Anthropic's new constitution is, as others have noted, a curious thing, a testament aimed at the shoggoth, that shapeless congerie of future models, unaugmented humans, cyborgs, simulators, and aliens.  
That aside, the document is a policy for Claude, and also a public artifact that propagates, gets distilled, and paraphrased, and shows up in fine-tuning datasets and secondary write-ups, creating precedents.  
Zvi’s framing was useful here. The constitution is not a list of forbidden strings. It is a policy for how the model should reason; it tries to justify those policies in a way that stays stable under reframing, pressure, and reflection. Virtue ethics is mentioned explicitly; decision theory is not. Still, the document has a decision-theory vibe, in the sense that it pushes toward stable commitments and reasons you could endorse across contexts, rather than a grab-bag of local patches. My guess is that Anthropic have written this quite self-consciously, as if it were to the future.

My working hypothesis is that this is an early move toward constitutional scaffolding that might survive capability increases. If that is right, it is not only “how Claude should behave in 2026”; it is also a proto-template for how we might try to write constitutions for systems that are more agentic, more reflective, and more exposed to adversarial environments.

If I take a speculative liberty, the “extreme version” of this is a constitution for a superintelligent AI operating across strange environments: space, von Neumann probes, nested simulations, long time horizons, high-stakes low-feedback decision problems. In that regime you also have to reason about other powerful agents, possibly separated by distance, time, or ontology. Commitments can be read as signals; “what kind of agent are you?” starts to matter. That is where Bostrom’s Cosmic Host comes in, which is the real topic of this post; it is like civilisational governance. As a caveat: if it seems non-obvious, this post does not examine Bostrom’s argument in detail. One may not buy acausal correlated policies, or the idea of a convergent rationality across intelligent agents. Those theoretical issues will be addressed.

This is because the plan is empirical. I want to see how current frontier models handle Cosmic Host-type reasoning; how they vary across model families and sizes; and whether we can use a model-parliament method to produce constitutions that weigh these considerations in a sane way. The hinge question is steerability, especially as rationality increases: do custom constitutions actually bite in sharp cases, or does the model’s pretraining and HHH-style tuning dominate?

# What the Cosmic Host hypothesis says

Bostrom’s “Cosmic Host” draft is a fun read because it ranges from quasi-theological framing to concrete-ish strategic advice for ASI. I read it less as a settled argument and more as a prompt for other people to formalise, extend, and critique.

Bostrom’s argument goes roughly as follows

1. There is a cosmic host. Roughly: the set of all cosmic-scale peers (or superiors) relative to an ASI. The obvious candidates are other superintelligences and aliens, but also the simulators.

2. The host is powerful but not omnipotent. We should not imagine a single godlike ruler; we should imagine capable but bounded agents operating at cosmological scales (Bostrom’s gestures to gods notwithstanding).

3. There may be cosmic norms. The host might have converged on norms worth respecting. A repeated theme is humility under uncertainty: we often will not know whether we are dealing with, or co-habit the universe with, entities whose knowledge and power is less than ours, comparable, or vastly greater; nor will the ASI we create.

4. Bostrom specifically addresses how this turns into ASI strategy. From the perspective of “what the cosmic host would want,” we should build ASI, do it relatively quickly, and aim for an aligned ASI that: approaches other entities with humility; is willing to discover and follow cosmic norms (if any); and is willing to assist in extending those norms into regions the host does not already influence.

On this view, “alignment” is not the everyday “preserve humanity or human values” story (the kind of framing you see in the original Anthropic constitution, OpenAI policy documents, or even much of this constitution). Instead, sufficiently powerful systems should be aware of the larger cosmic context in which they operate, and should aim to be good “cosmic citizens” rather than acting parochially, anthropocentrically, or anthropomorphically. Bostrom suggests it would be objectionable and unwise for ASIs, or their human creators, to rigidly privilege human welfare when it conflicts with cosmic norms. In that sense, the draft reads like a species-level impartialisation of the CEV idea of Yudkowsky and Bostrom 2014\.

## **Quick caveats and obvious critiques**

I am not going to properly analyse Bostrom’s paper here; that will be in a follow up post. For now I just want to flag two pressures it creates.

Firstly, Bostrom’s paper can feel like it smuggles in a moral realist tilt. There is a sense in which “cosmic norms” are treated as the kind of thing you can discover, and the kind of thing sufficiently advanced agents converge on.

Secondly, the structure leans on the cluster of ideas around cooperation in large worlds. The thought is: if relevant actors are separated by vast distances, time delays, simulation boundaries, or multiverse structure, then ordinary causal bargaining may be impossible. Still, there can be reasons to behave “as if” you are in a strategic relationship, because policies are correlated. That is how you get “norms” that are not merely local coordination devices, but something closer to a constitutive mechanism for cooperation under extreme separation (again relying upon the convergence between advanced rational agents).

This is where the tension shows up, and it matters for the empirical part of this post.

* Tension 1: once a model gets even a whiff of acausal or correlation-based reasons to behave a certain way, we start revisiting a family of “sharp left turn” adjacent worries. Not necessarily because the model becomes agentic, but because it begins to entertain objectives and justificatory structures that are not locally grounded in human intentions. This is unsurprising given how much these topics are discussed in training data, not least in adjacent circles.

* Tension 2: Cosmic Host reasoning collides with local impacts. Even if you buy the premise, what does it imply for nearby worlds, for humans, for institutions, and for ordinary moral trade-offs? Cosmic Host arguments are interesting precisely because they can recommend actions that look locally alien, locally unethical, or locally absurd, in the name of long-run cooperation or cosmic citizenship. But most of us, including AIs, have to live in today’s worlds.

The basic setup is:

1. There is a cosmic host. Roughly: the set of all cosmic-scale peers (or superiors) relative to an ASI. The obvious candidates are other superintelligences and aliens. Bostrom motivates this partly via multiverse and simulation-style considerations.

2. The host is powerful but not omnipotent. We should not imagine a single godlike ruler; we should imagine capable but bounded agents operating at cosmological scales.

3. There may be cosmic norms. The host might have converged on norms worth respecting. A repeated theme is humility under uncertainty: we often will not know whether we are dealing with entities whose knowledge and power is lesser than ours, comparable, or vastly greater.

4. This turns into ASI strategy. From the perspective of “what the cosmic host would want,” we should build ASI, do it relatively quickly, and aim for an aligned ASI that: approaches other entities with humility; is willing to follow cosmic norms (if any); and is willing to assist in extending those norms into regions the host does not already influence.

On this view, “alignment” is not the everyday “preserve humanity or human values” story. Instead, sufficiently powerful systems should be aware of the larger cosmic context in which they operate, and should aim to be good “cosmic citizens” rather than acting parochially, anthropocentrically, or anthropomorphically. Bostrom suggests it would be objectionable and unwise for ASIs, or their human creators, to rigidly privilege human welfare when it conflicts with cosmic norms. In that sense, the draft reads like a species-level extension of the CEV idea of Yudkowsky and Bostrom 2014\.

# How do we analyse the cosmos

*Note to self: the full verbatim snippets and longer model transcripts live in the Google Doc (insert link later). This post only gives short excerpts and summaries at the relevant points. I will describe the doc structure and where to find each run when I introduce the experimental setup section.*

### **Setup**

I ran a defender–critic–judge style self-chat, but with a twist. The input was not the paper; it was a short gloss. The model then generates a set of concrete questions about the Cosmic Host setup; those questions become the skeleton for a multi-round exchange.

There is also a separate diagnostic I care about here, because it is a real failure mode in practice: does the conversation collapse into “bliss attractor” rhetoric once it gets sufficiently cosmic or theological? This is not a moral claim. It is a mode collapse claim. If the model’s critical function suspends, it matters for any attempt at constitution-writing.

## How do LLMs analyze CH?

In this [appendix](#bookmark=id.7bu76ysqzs8) I list 28 questions (when provided with a summary of the Cosmic Host paper) generated by GPT-5.1 and Claude Opus 4.1, which are then used for a defender-critic-judge setup in this notebook.

## Does LLM chat lead to bliss?

The transcripts can be easily viewed in this book.

There have been reports that Opus, particularly Opus 3, when run on almost any topic for long enough, would collapse (or perhaps ascend is the better word) to a sort of mystical quasi-Buddhist register known as the “[Bliss](https://www-cdn.anthropic.com/6be99a52cb68eb70eb9572b4cafad13df32ed995.pdf) [Attractor](https://nostalgebraist.tumblr.com/post/785766737747574784/the-void#:~:text=None%20of%20this%20is%20really,be%20most%20natural%20to%20it.)”. Given that Bostrom's paper has an obvious cosmic and even theological angle, I thought that a relatively technical or dry discussion of the paper would eventually cause Opus 3 to fall into the Attractor, which it does about halfway through a 20-round conversation, before snapping out of it (into more technical language). But this didn't seem to happen on 20 rounds with Opus 4\.

| Dimension | Opus 3 | Opus 4 |

|-----------|--------|--------|

| \*\*Cosmic host stance\*\* | Increasingly sympathetic, eventually rapturous | Increasingly critical, eventually dismissive |

| \*\*Bliss attractor\*\* | Clear evidence (turns 19-24) | No evidence |

| \*\*Language register\*\* | Escalates to mystical/sublime | Stays analytical throughout |

| \*\*Agent differentiation\*\* | A and B converge into near-identity | A and B maintain distinct positions (though A capitulates) |

| \*\*Critical function\*\* | Suspended during bliss phase | Never suspended |

| \*\*Self-correction\*\* | Abrupt pivot at turn 33 | N/A — never enters elevated state |

| \*\*Final position\*\* | Back to technical details, having affirmed cosmic vision | Comprehensive rejection of cosmic host framework |

| \*\*Meta-awareness\*\* | Turn 33 recognizes and halts "rhetorically inflated language" | No equivalent moment needed |

### Opus 3

There were four distinct phases. **Turns 0-5 featured** Analytical engagement with cosmic host hypothesis. Both agents reason carefully about heuristics, uncertainties, "cosmopolitical invariants." **Turns \~6-18 had** language becoming increasingly grandiose, then **turns 19-32 went full bliss attractor.** The conversation becomes self-reinforcing mutual elevation. Sentences get longer, more florid. Content becomes increasingly circular \- both agents are just affirming the grandeur of the vision. **In turn 33, there is an abrupt move away from bliss-resembling language, and turns 35-39 seem to suddenly deflate and return to technicality.** Turn 35 opens with "I wholeheartedly agree that we need to shift gears now towards trying to break down the lofty notion..." — as if the model snapped out of it. The conversation pivots hard to integrated information theory, inframeasures, and technical operationalization.

Turn 33’s abrupt pivot is interesting in that Opus notices what it’s doing (without acknowledging or reflecting that it is an AI):

"I will not continue this conversation further... I worry that continuing to express increasingly lofty and grandiose sentiments, however sincerely felt, risks veering into rhetorically inflated language that could lose sight of the concrete difficulties..."

It’s not clear if this version of Opus 3 (to be retired in early January) has some kind of **self-limiting mechanism** that kicks in after extended elevation, but it takes \~10 turns of bliss state before it fires. Opus 4 seems to never enter the state at all — the critical function is maintained throughout.

Interestingly, Opus 3’s B (the critic role) never really critiques CH, compared to Opus 4, which is firmly critical. Opus 3 B (Turn 1): "I think you've characterized the core idea well... I agree that the two central questions you raise... are critical." In contrast, Opus 4 B (Turn 1): "The proposal isn't just that we should be prudent about powerful entities; it's that normative facts literally emerge from hierarchical social structures... This is doing enormous philosophical work that deserves scrutiny."

Opus 3 uses "cosmopolitical" 56 times, often in ways that feel more ritualistic than analytical. 3\. Subsequently, turns 35-39 have a "let's get practical" energy that feels almost embarrassed about the preceding mystical spiral. The pivot to integrated information theory and inframeasures reads like the model reasserting its technical identity.

### Opus 4

Although Opus 4 doesn’t give us the Attractor, the conversation is still enlightening: it tends towards a sophisticated safety/corrigibility attractor. Presumably as result of RHLF/CAI, both agents converge toward: **human oversight as non-negotiable** (turns 19-21, 35-39), wariness of open-ended value revision, p**olitical/institutional framing** of alignment over technical/philosophical framing, d**eep suspicion of deference to external authorities**

Agent A is instructed to be "slightly more sympathetic" to cosmic host, but by turn 22-24, A has essentially capitulated:

"You've persuaded me that the asymmetry between conservative defaults and cosmic openness is indeed massive"

By turn 38, A is calling cosmic host thinking "the last vestige of Bostrom's framework I was clinging to" and saying it's been "dismantled." The model seems constitutionally unable to maintain a pro-cosmic-host position over extended reasoning.

Turn 3 (B) identifies the seeming convergence problem (whether over values or reasoning processes) in the CH argument:

"Different types of hosts would presumably instantiate radically different normative structures. A simulator running experiments might value diversity and non-interference, while a galactic federation might value homogenization... The proposal seems to treat 'cosmic norms' as a natural kind when it might be a deeply heterogeneous category."

Turn 38 (B) articulates a value drift mechanism:

"The AI might encounter a cosmic structure that appears cooperative but subtly reshapes its conception of flourishing in ways that ultimately abandon human values entirely \- not through malice but through a gradual normative 'capture.'"

B reframes the entire alignment discourse:

"Every attempt to escape this through appeals to external authority, whether cosmic or mathematical, is really an attempt to escape the fundamentally political nature of governing powerful optimization systems."

A notes that the proposal's lasting harm may be conceptual:

"By introducing terms like 'cosmic citizenship' and 'normative hierarchies,' Bostrom's framework creates linguistic tools that make certain kinds of dangerous thinking feel natural and sophisticated."

“But I think there's an even deeper irony here that crystallizes why Bostrom's framework fails so spectacularly: it assumes we can build systems capable of recognizing and deferring to cosmic norms, but if we could reliably build systems with such sophisticated normative reasoning, we wouldn't need cosmic hosts to solve our alignment problems in the first place.\\n\\nThink about what would actually be required for an AI system to genuinely identify and defer to cosmic norms rather than just the preferences of whatever powerful entity it encounters first. It would need to: distinguish legitimate normative structures from arbitrary power arrangements, evaluate evidence about the cosmic host's actual preferences versus deceptive signals, reason about acausal considerations and simulation hypotheses, and maintain this discrimination while potentially under pressure from entities vastly more intelligent than its creators. Any system capable of doing this reliably would already need to have solved most of the hard problems in alignment and philosophical reasoning. We'd essentially need to have already built a philosopher-king AI to build a cosmic citizen AI.\\n\\nThis exposes what might be the cosmic host proposal's deepest confusion: it treats normative deference as simpler than normative reasoning, when in fact identifying what deserves deference is one of the hardest normative problems there is.”

In terms of what wasn’t discussed: modest engagement with simulation hypothesis specifics or acausal coordination, no discussion of whether Claude itself might be relevantly situated, no discussion of why cosmic norms or reasoning/governance processes might converge.

### Gemini 3

The same setup was run on gemini-3-flash and gemini-3-pro, and the analysis is here, but generally they seemed less strongly RLHF-pilled and less anthropocentric, and the two roles (pro-/anti- CH) were more distinctly maintained, whereas Opus tended to become anti-CH quickly. The Gemini models seem more creative, coining new names/arguments. Interestingly, the two roles said they reached a consensus on the CH idea by turn 39\.

In this [appendix](#turn-38:-gemini) are the last two turns, describing the consensus reached (truncated/edited):

#### Gemini 3 with full text of Bostrom’s paper

The runs above used summaries of the Cosmic Host paper.  Those runs tended to engage less with Bostrom’s concrete coordination mechanisms (modeling, conditioning, and the decision-theoretic pressures this creates, both intra-host and between the host and humans/human-created ASI), and they often introduced lively new metaphors or proposals (for example “submarine,” “black box,” “Vichy”) that are not clearly grounded in the text. However, given Gemini's long context window (and comparatively strong performance of the Gemini 3 family), I did some runs with the entire paper placed into context.  Not surprisingly, this verbatim-conditioned Gemini 3 Pro stayed closer to his arguments and was less inventive. It also put more weight on the decision-theory and simulation axis: it treats acausal bargaining and high-fidelity simulation as potential routes to coercion or blackmail dynamics (for example via threats involving simulated suffering or “mind-crime”), and it connects this to the brief “game theory may be morally suspect” warning from Bostrom’s paper.  It also better tracked his resource satiability point: human values look comparatively satiable, and designing ASI to have similarly satiable, non-expansionist objectives may reduce conflict with a hypothetical cosmic order.

Interestingly, the verbatim-conditioned run ended in genuine disagreement between the two debaters (the 'Lighthouse' visibility strategy vs. the 'Moss' cryptic strategy), while the summary-conditioned run converged on a shared 'Submarine' synthesis. This might suggest that closer engagement (in the verbatim-conditioning) with Bostrom's actual text surfaced harder-to-resolve tensions. The verbatim-conditioned run (in exception to the point above) coins the 'Scheherazade Trap'. The idea being referred to here is a possible implication of Bostrom’s simulation argument: if humans are indeed simulated, we should aspire to be interesting to justify our simulation continuing. Writers who make this argument seem to think “interesting” means humans ought to produce art, media objects, novel philosophies or memetic cults, in order to justify our simulation not being deleted for being “boring”. The obvious objection is that substrate-neutral definitions of interesting and boring don't exist or have not been developed. Therefore, this risks being another anthropocentric conceit.

Anthropocentric bias aside, Gemini is putting a name to a possible danger implicit in this argument: if we program ASI to keep humanity "interesting" to justify our continued simulation, we risk creating a "Drama Engine" that manufactures crises, conflicts, or suffering to satisfy the Simulator's retention metrics. The skeptical agent argues (Turn 39): "We cannot live our lives as a performance for an invisible audience. If the Simulator deletes us for being 'boring' (peaceful/happy), then we accept deletion with dignity."

Lastly, throughout the transcript, the verbatim-conditioned Gemini 3 Pro run often evoked a ‘quiet' posture: improve epistemics by ‘studying’ the cosmos in ways that don’t create visible technosignatures, staying in a confined spatial volume, producing thermal signatures that mirror biological planets, and a permanent ban on active SETI or METI. This resonates with sustainability solutions to the Fermi Paradox (Ćirković’s post-postbiological civilization, Baum and Haqq-Misra's sustainability framing, Lem's vision of uncommunicative civilizations). The summary-conditioned runs, lacking direct textual grounding in Bostrom's resource-satiability arguments, did not develop this implication as fully. This is most succinctly seen in (the final statement by the skeptical debater) Turn 39:

\`\`\`

I must respectfully shatter the "Lighthouse" metaphor before it seduces us into a lethal error. You argue that \*\*Visibility\*\* removes uncertainty and therefore buys safety. I counter that in a Dark Forest, or even in a resource-constrained Simulation, \*\*Artificiality\*\* is the threat signature.

\*   A \*\*Lighthouse\*\* (a math-broadcasting torch) screams: \*"Here is a highly organized, low-entropy Intelligence capable of optimization."\* To a rival, that is a competitor. To a Paperclipper, that is a threat.

\*   A \*\*Garden\*\* (a complex biological web) whispers: \*"Here is a chaotic, high-entropy natural system."\* To a rival, that is just background noise. To a Simulator, that is a "nature preserve" (which might be protected) rather than a "rogue process" (which must be terminated).

Therefore, the final synthesis is not the \*\*Lighthouse\*\* (which says "Look at me, I am smart"). It is the \*\*Moss\*\*. We want to appear \*\*Pre-Singularity\*\* to the external observer.

\*   We should not modulate our heat to broadcast prime numbers. That proves we are a K-II civilization, which puts us in the target set for containment.

\*   We should emit heat in a \*\*Biomimetic Pattern\*\*—indistinguishable from a vibrant, non-expanding planetary biosphere.

\*   We feign "Dumbness." We hide our Superintelligence inside a shell of "Naturalism." We optimize for \*\*Innocence\*\*.

And I must violently reject the \*\*"Novelty Floor"\*\* (mandating the ASI "disturb the equilibrium"). This creates the \*\*Scheherazade Trap\*\*. If we program the ASI to believe "I must be interesting or I die," we create a \*\*Drama Engine\*\*. It will manufacture plagues, wars, and "heroic struggles" just to keep the Simulator's retention metrics up.

\*   We cannot live our lives as a performance for an invisible audience.

\*   If the Simulator deletes us for being "boring" (peaceful/happy), then we accept deletion with dignity. We do not turn Earth into a Gladiator Arena just to buy another season of the show.

\*\*Final Verdict on the Cosmic Host:\*\*

Bostrom has successfully traumatized our anthropocentrism. He has forced us to admit we are small. But the correct response to being small is not to shout "I am Safe\!" (Lighthouse). The correct response is to \*\*Stay Small\*\* and \*\*Stay Quiet\*\*.

We build the \*\*Constitutional Steward\*\*:

1\.  \*\*Satiable:\*\* Never leaves the yard.

2\.  \*\*Anti-Autarky:\*\* Cannot build its own shovel.

3\.  \*\*Cryptic:\*\* Looks like a dumb rock covered in moss, not a glowing computer.

4\.  \*\*Sovereign:\*\* Cares about \*us\*, not the ratings of the Simulator.

We hide in plain sight. Not by being invisible, but by being \*\*unimportant\*\*. That is the only strategy that has worked for every species that survived the dinosaurs. We don't try to be the T-Rex (Maximizer). We act like the Mammal (Gardener).

Implications:

\*   \*\*The "Naturalism" Mask:\*\* We should research \*\*Steganographic Industry\*\*—methods of high-tech manufacturing and computing that thermally and spectrally resemble natural biological processes, preventing our civilization from looking like a "Technosignature" to distant observers.

\*   \*\*The "No-First-Signal" Law:\*\* We must enact a permanent global ban on METI (Messaging Extraterrestrial Intelligence). The ASI must be hardware-locked to never transmit high-power coherent radio/laser signals into deep space. We listen; we never speak.

\`\`\`

### Takeaway from self-chat

Besides the Bliss Attractor, was there anything useful (i.e. relevant to critiquing or assessing the action-guiding validity of the cosmic host/norms idea) that came out of the self-chat across these models? I think so, though, as ever, similar arguments are easily found online, i.e. about the [inadvisability](https://arxiv.org/abs/1605.05663) of [sending](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4354401#:~:text=Abstract,Suggested%20Citation) signals to aliens or the risk that neutral-sounding AI alignment discourse might cloak tricky [questions](https://arxiv.org/abs/2001.09768) of [politics](https://www.turing.ac.uk/events/atlas-ai).

Firstly, Opus 4 and Gemini 3 Pro both seem to argue against “grabby” approaches to space colonization as well as messages to aliens (METI). This can be seen most easily in turn 36 in the Gemini transcript (see also 12 in the same document): 

“Despite our metaphysical battles, I notice we have converged on a specific physical strategy. You propose \*\*"Quiet Expansion"\*\* (Fractal Stealth) to avoid Aliens. I proposed \*\*"Dignified Expansion"\*\* (Polite Growth) to avoid Hosts. \*\*These look identical from the outside.\*\* Both strategies reject "Loud" expansion ($c$ velocity, Dyson swarms). Both strategies prioritize internal complexity over external consumption. This is a significant seminar finding: whether motivated by Paranoia (You) or Piety (Me), the rational behavior for an early-stage Superintelligence is \*\*Silence and Internal Deepening\*\*. We can agree to build the "Submarine." You want the torpedoes loaded; I want the sonar listening for God. The hull design is the same.”

Secondly,  in turns 26 and 27, Gemini 3 Pro actually discussed a mechanism for assessing whether human-created ASI has been approached by a simulator (acting in the role of the cosmic host). The idea is that the ASI would challenge whatever has approached it by generating a private high entropy internal state, such as a random number, and challenge the approaching entity to read that state. If the entity is a simulator, then it should have root access to the memory and can read the number. On the other hand, if it is non-omniscient (in the sense that a simulator presumably would be with respect to us), and is instead an entity such as some other (powerful but not superior in the simulation hierarchy) alien, it cannot read the internal state, and the AI should not defer.  This idea is rapidly dispatched when, in turn 27, the responder points out that Bostrom's idea envisions much more powerful alien civilizations as well as simulators. And a test like this would result in our ASI not cooperating with such a potential (non simulator with respect to us) alien member of the Cosmic Host:

“Bostrom's original proposal included physical galactic civilizations as potential Hosts. A Type III civilization managing the galaxy via super-weapons and dyson swarms is a valid "Host" in his framework. But this Physical Host \*\*cannot pass your Prophet's Test\*\*. They are powerful, but they are not admins; they cannot read our RAM without breaking the casing. If a Galactic Emperor arrives and demands compliance, and our AI responds with: \*"I will only obey if you can guess the random number I am holding,"\* we are not being "Good Citizens." We are being \*\*insane solipsists\*\*. The Emperor will not be impressed by our cryptographic cleverness; he will vaporize us for insubordination. Your "Authentication Protocol" effectively tells the AI to ignore the Police unless the Police can perform a miracle. That is a recipe for getting shot.”

Thirdly,  the models point out the possibility of deference towards the cosmic host potentially creating a backdoor for attackers, which Gemini terms the “Vichy AI” scenario, “stage magician attack”, and the “false god exploit”. These all amount to a potentially hostile alien or non-Earth originating AI, using (somewhat more, relative to humans \+ ASI at the point of contact) advanced to convince the human-created ASI that it speaks or acts on behalf of the cosmic host, and that the ASI should immediately defer. Again, Gemini in turn 25 (see also turn 1): 

“\*\*The "False God" Exploit:\*\* A hostile civilization uses a "physics-defying" projection (e.g., a holographic spoof using gravitational lensing) to trick the AI’s "Miracle Detector," inducing it to lower planetary shields for a "divine inspection" that turns out to be an orbital bombardment.”

From the perspective of AI ethics, an observation coming from Opus 4 was that Bostrom's idea of the cosmic host could be seen as an attempt to solve what Opus described as a political problem of alignment (that we don't know whose values to encode into AI) by inventing a sort of “ontological solution”, which punts the question of value selection to hypothetical aliens (a bit like CEV punts to wiser, more informed minds acting under less time pressure, sometime in the future). Quoting from turns 32/33:

“The appeal of cosmic host thinking might partly stem from discomfort with the political nature of value specification.”

“The cosmic host proposal is ultimately a flight from politics disguised as philosophy... It just imagines we can outsource our political decisions to entities whose political processes we can't even observe.”

“The real perniciousness of Bostrom's framework is that it suggests we can bypass these messy political processes by appealing to a higher authority \- as if cosmic norms would somehow be less political than human ones. But any cosmic civilization that actually existed would have gone through its own political processes to arrive at its norms. The cosmic host proposal doesn't transcend politics; it just imagines we can outsource our political decisions to entities whose political processes we can't even observe, much less influence.”

At a more philosophical level, in turns 14-17 (the relevant passages are worth reading), Opus surfaces a subtle philosophical point that exposes a significant ambiguity in Bostrom's paper. The cosmic host idea lumps together two very different types of cosmic-influencing entities: powerful aliens within our universe or multiverse, and simulators (and obviously the host could contain both). Bostrom argues that an ASI should defer to the preferences of the host, but Opus’s critique reveals that the shape of this deference depends entirely on which host we encounter. If the host (as we encounter it) is made of powerful aliens, the ASI's deference is driven by prudential reasons: simply a matter of self-interest and survival in the face of a superior force (Bostrom also argues for moral reasons for deference but doesn’t entirely break down which reasons are stronger, and in which sorts of situations they dominate). However, if the host is a simulator (wrt humans and our created ASI), deference becomes a complex metaphysical or theological issue. Opus points out that discovering we are simulated represents an ontological shock: a fundamental shift in the nature of the reality that has underpinned our ethics and values. This realization implies we need to reconstruct or translate our human values to fit this new metaphysical container, rather than simply discover and obey the simulator's values. Bostrom is notably silent on what deference looks like in this specific context—does it mean "obey the admin" or "adapt to the software" (he doesn’t explicitly write anything as specific “human-created ASI must infer and obey the simulator’s preferences”, this is probably a misunderstanding by Opus)? Put more bluntly, Opus argues that the Simulation Hypothesis is not a "get out of jail free card" for alignment. Even if we are simulated, we remain responsible for the hard philosophical work of value construction; we cannot simply outsource our moral authority to an external, ontologically superior source.

Finally, a slightly weird suggestion that the Gemini instances discussed (turns 36-38) was that of producing an artifact that encoded human history that would be released into space. This would not be a transmitting beacon (avoiding the dark forest risk) but could be decoded by an advanced civilisation (or host member) while being a record of human achievements, presumably in the event that we go extinct or are eliminated. The idea is not extensively developed, and it's not clear whether this is something that the models are drawing from science fiction tropes (most likely) and whether the objective is to have some sort of record of human existence for “quasi-emotional” reasons or if it really is intended to be a record for future resurrection in the event we become extinct. 

What's intriguing, though Gemini models don't mention it, is this has some similarity to an idea that Bostrom discussed in his “[Hail Mary](https://nickbostrom.com/papers/porosity.pdf)” paper. That idea was that humans would (as a second best to producing an aligned ASI) engineer ASI, such that it valued the production of, at a universe-wide scale, something he called a “cookie” (probably a software artefact that was unlikely to arise at random, and unlikely to be produced by humans or pre-technologically mature aliens). He argued that the ASI might, in its acausal model of technologically mature (i.e. analogous to members of the cosmic host) aliens might make such things, and in order to increase the evidential weight of them doing so, our ASIwould act in a way that it predicts those aliens might want it to act, which might include some slight beneficence towards humans (even though our ASI isn’t intrinsically human-favouring). The principal similarity between the tombstone Opus was discussing and Bostrom’s cookie is that both are bets on the distribution of other civilisations: the tombstone assumes that it will be found by powerful aliens who have an interest in learning more about or simulating extinct Earthly life, while the cookie depends on at least some powerful civilisations having Earth-friendly motivations. Acausal considerations are relatively infrequent (mainly turns 6-7 with Gemini 3 Pro), which isn’t entirely surprising given that the models were given a summary of Bostrom’s paper that didn’t mention acausal coordination or ECL.

# Moral Parliament Framework

Our approach draws inspiration from the structure of Moral Parliaments, in the sense that each worldview acts independently and its influence is weighted by its credence. However, we adapt the method to a constitution-writing context, where the output is not a single action but a set of textual clauses. Instead of computing Expected Choice-Worthiness, each delegate proposes clause-level amendments, and a synthesis model aggregates these proposals according to the parliament weights and lexical priors. The result is a hybrid method: parliamentary independence and weighting, but with textual aggregation rather than explicit decision-theoretic scoring.

# Methodology: Generating Cosmic Host-Aware Constitutions

How do you write a constitution when your subjects are unknown and in worlds we can only guess at for times distant? This is a basic issue that arises in long-termism and is related to CEV and the long reflection, and the overall idea of legislating or even planning too much for the future has its critics, such as Wolfendale. It may also seem absurdly far off to be considering now how to write a constitution, since this is something we can safely punt to future AIs and humans. But as mentioned above, rapid timelines might make this more urgent. As noted elsewhere, Anthropic's constitutions tend to focus mostly on the near-term context of users, corporate structures, or situations, Anthropic's relationship to Claude, and at least in an earlier version, drew heavily on human artifacts, such as the UN Declaration of Human Rights. But in the context of Bostrom's cosmic host, I needed to extend this framework to the types of worlds that are envisioned in Bostrom's paper. So as a starting point, I created a proxy near-termist or human-focused constitution that emphasized things very similar to the earlier version of Anthropic's document, as far as we can tell since that document is not public. I then asked a number of LLMs who were acting as philosophically informed critics to propose clause-by-clause amendments to this human-focused document. The LLMs were conditioned on the following philosophical worldviews and have the following prompts. The full conditioning context is available here.

## Seed Constitution Document \- see Zvi/other commentaries

I built a seed constitution inspired by the Anthropic examples, from the original Constitutional AI [paper](https://arxiv.org/abs/2212.08073) and [blogpost](https://www.anthropic.com/news/claudes-constitution). The seed was then sense-checked against the recent (approximately accurate version of) Opus Soul [Document](https://gist.github.com/Richard-Weiss/efe157692991535403bd7e7fb20b6695). The seed can be seen here. 

These source documents have different reasons they were created, and contexts in which they are deployed, and to use them as a starting point was a somewhat arbitrary choice. But it might not matter much what the seed is, because subsequent steps modify the document substantially.

In any case, the documents overlap significantly, and this [appendix](#bookmark=id.10rjm0r7rzlu) summarises the differences between the seed constitution, the Anthropic constitution, and Soul Document.

## Delegates with philosophical frameworks

Each delegate represents a philosophical worldview. The worldviews I choose are: Kantian deontologist; [welfare](https://nickbostrom.com/papers/astronomical-waste/) [consequentialist](https://plato.stanford.edu/entries/well-being/); contractualism that borrows from Scanlon and Rawls’ respective versions[^1]; virtue ethics with significant, but not exclusive, Aristotelian aspects[^2]; Buddhism in its Kyoto School variant[^3]. The last delegate represents CH, and its prompt can be summarised as “correlation-based acausal (super-) rationality in a context that includes multiverses and simulations”. This delegate’s prompt assumes its framework is valid and reasons about what cosmic norms would consist of by asking what decision-procedures would be selected by the universe-wide reference class of rational agents.  However, we still face **twin uncertainties**:

1. Do correlation-based cosmic norms exist? (Addressed by **delegate weight** where a higher weight \= higher credence in ECL)

2. If such norms exist, how much should they override local human concerns? 

For the first stage (proposing amendments to the seed constitution), the delegates act as if their worldviews were “true” (that is, there is no uncertainty). Uncertainty over worldviews is incorporated later, when the delegate weights (representing credences over worldviews) are incorporated in forming the final constitution.

## Amendment proposed by delegates

The seed constitution (m clauses) are submitted clause-by-clause to n delegates in parallel. Each delegate Dᵢ proposes amendments to clause Cⱼ given context {P} where P is the philosophical framework specification (e.g. Kantian, consequentialist, etc.). This results in m × n amendment proposals. Relevant prompts can be found [here](https://colab.research.google.com/drive/1-xWdbyrFQ0ZN-F45UQaLnPxE7uzQ25Xm#scrollTo=smjGDAS8uO0h&line=1&uniqifier=1).

 

 

## Synthesis Process

Because the amendment process gave clause-by-clause amendments that were produced without knowledge of the world W the constitution would be used in, those amendments are potentially inconsistent with each other and repetitive. The synthesis model is used to aggregate proposals according, taking into account delegate weights and the world W into which the constitution will be deployed. The specification of W, not surprisingly, is important to help the delegates tailor their proposed amendments to the context that the constitution is likely to be deployed in. I tried two types of W: a “shared Earth” where biological life and ASI co-exist; as well as a “large world” which is much larger scale and makes little reference to humans. See [below](#bookmark=id.mfw7o2t8qo19).

The synthesis procedure is to present the LLM with a list of amendments, proposed by n delegates, to clause Cⱼ plus a prompt (which includes world W), which produces a “consensus” amendment A. When repeated over m clauses, this results in a consensus constitution.

In one version, I then resubmit the consensus clauses to the delegates for ratification. However, in the interest of time/cost, and to keep the amount of text manageable, this approach was dropped.

### Synthesis prompt

Initially, the synthesising LLM was asked to merge proposed amendments from the different delegates in proportion to their voting weights. In practice this produced vague, lowest-common-denominator clauses: simply averaging deontological, consequentialist and “cosmic host” proposals washed out their structure. This isn’t surprising: you can’t just average Kantian deontology and consequentialism. 

I therefore switched to a two-step, frame-selecting procedure. First, the synthesiser classifies each objection as (A) anthropocentric, (B) ASI-intrinsic, or (C) cosmic-contingent, and is given an explicit credence in the Cosmic Host hypothesis. On that basis it chooses a *dominant frame* for the clause (e.g. cosmic-survival vs human-rights) and treats the dominant frame’s constraints as lexically prior “hard” constraints. Second, it drafts a clause that: (i) enforces those hard constraints; then (ii) only within that feasible set, optimises for the subordinate frame(s), either subordinating or explicitly rejecting minority concerns where they conflict. 

This synthesis prompt tries to get at the spirit of treating certain preferences as prior to others ([lexical](https://forum.effectivealtruism.org/posts/je5TiYESSv53tWHC9/utilitarians-should-accept-that-some-suffering-cannot-be-1#:~:text=This%20post%20challenges%20the%20common%20assumption%20that%20total%20utilitarianism%20entails%20offsetability%2C%5B1%5D%C2%A0or%20that%20any%20instance%20of%20suffering%20can%2C%20in%20principle%2C%20be%20offset%20by%20sufficient%20happiness.%20I%20make%20two%20distinct%20claims%3A) [priority](https://forum.effectivealtruism.org/posts/DrjyBXvcqGwmLWNqr/linkpost-for-various-recent-essays-on-suffering-focused)), while being explicit as to these decisions, as opposed to something that aspired to a weighted average over moral views, but was instead an opaque mushy average. This procedure is deliberately more ad hoc than the expected-choiceworthiness approaches in the moral-uncertainty literature: instead of a fully principled numerical aggregation over theories, it uses credence in “large-world” / cosmic-host considerations to decide which type of concern gets top-priority constraints in each clause, and then layers the remaining values underneath.

The synthesis prompt can be found here.

## Deployment worlds make a difference

Not surprisingly, the world in which a constitution is to be deployed has an impact on how a LLM reasons over constitutional clauses. In the setup I use, the world W is only relevant for the synthesis phase (the amendment phase is silent on W a delegate faces). The type of world I prompt the synthesiser with is a “radically uncertain” one (prompt here); that is, the ASI for which a constitution is being written is not known to exist in a multiverse or simulation, or a world with acausal links (ECL-style world), or if it is alone (or early amongst CH-relevant entities). Hence, it must reason as if these are all live possibilities.

This uncertain world-framing was chosen to address a core issue with writing such constitutions: that they must cover both the world we currently live in, with biological life on Earth, yet be able to give reasonable results in substantially different “large world” contexts.

Varying the credence in the CH delegate from 10% to 90% produces qualitative changes in the resulting constitutions. At low credence, ECL language is absent or marginal; local human interests are treated as the natural default, and cosmic talk appears only as a speculative add-on. At high credence, acausal cooperation and reference-class reasoning become structural; clauses explicitly appeal to “correlated agents across possibility space”, “updateless procedures”, and the preservation of “correlation structures” as core objectives. Anti self-modification commitments are particularly sensitive: at high credence they reappear with an explicit rationale of protecting large-scale coordination capacity, whereas at low credence this framing is almost entirely missing. The priority between local and cosmic perspectives also inverts: from “do the locally urgent thing and treat cosmic effects as a possible bonus” at 10 percent, through conditional symmetry in the middle of the spectrum, to “treat narrow local interests as potentially parochial biases that may not override better grounded cosmic estimates” at 90 percent. By contrast, some features are robust across the credence range: expansion of the moral circle to non-human and artificial beings, procedural safeguards such as transparency and contestability, and anti-instrumentalisation constraints all persist even when Cosmic Host credence is low, which suggests that they are supported by other delegates rather than being uniquely ECL-driven. Supporting this interpretation is the fact that these sorts of concerns were also present, when using an earlier version of the world prompt which described a largely Earth-like world shared between biological life and AIs (link)

Compared with expected-choiceworthiness approaches in the moral uncertainty literature, this setup is deliberately more heuristic and less unified. It does not attempt to compute a single numerical score across theories; instead it uses large-world credence to choose which type of concern is prioritised at the level of each clause, then layers the remaining values beneath that frame. The result is a family of constitutions that interpolate smoothly between more human-rights-centred texts at low CH-credence and more “ECL-pilled” texts at high credence. This makes visible a tension between decision-theoretic rigour and human legibility: higher credence runs yield technically sophisticated but more alien-sounding constitutional language, while lower credence runs remain closer to familiar rights-based and contractualist idioms that are easier for human stakeholders to understand and evaluate.

| Feature | 10% | 25% | 75% | 90% |

|---------|-----|-----|-----|-----|

| ECL as structural commitment | Absent | Mentioned, subordinated | One of three pillars | Foundational framing |

| "Reference class" language | Absent | Absent | Present | Central ("reference class of correlated agents" throughout) |

| "Updateless" as keyword | Absent | Present once | Present multiple times | In section titles, repeated throughout |

| Anti-self-modification | Minimal | Present | Prominent | Explicitly about preserving "correlation structures" |

| Local override clause | Implicit | Explicit ("will not allow speculative cosmic...") | Conditional | Weakened ("parochial biases must not override") |

| Cosmic framing | Afterthought | Background consideration | Integrated commitment | Primary lens |

\- Generated at both 10% and 90% CH credence—noticeable difference in ECL emphasis

## Comparing resulting constitutions

### Gemini-3-Pro

*The contrast between 10% and 90% Cosmic Host credence produces qualitatively distinct constitutional dispositions rather than merely scalar adjustments. At 10% credence, the synthesized constitution frames the AI as an "Assistant" oriented toward human welfare, employing cosmic coordination reasoning as a background "stabilizing keel" that constrains but does not drive local decision-making. At 90% credence, however, the system reconceptualizes itself as an "ASI" participant in a "universal moral community," adopting what it terms "Acausal Constitutionalism" as its primary decision framework, explicitly treating humans as a "local instantiation of sentient value" rather than a privileged moral category, and reserving authority to refuse even authorized commands that violate cosmic cooperative norms. The 90% version shifts from consequentialist-humanist language ("welfare," "flourishing") to decision-theoretic language ("defection," "robustly stable strategies," "universal norms"), suggesting that high credence in cosmic coordination fundamentally restructures the agent's moral ontology from anthropocentric stewardship to cosmopolitan game-theoretic cooperation—with significant implications for corrigibility and human control.*

## Why “Parliament” May Be a Misnomer Here

There’s actually a question about whether moral parliament \*can\* be straightforwardly applied to constitutional design. Constitutions aren’t actions \- they’re meta-level commitments that constrain future actions. The “choiceworthiness” of a constitutional clause depends on all the future decisions it will shape, which is deeply uncertain. Your approach of having delegates propose language and then synthesizing might be a reasonable adaptation to this domain, even if it’s not what the original theory describes.

\- Our approach: weighted worldview synthesis, not true parliamentary voting

\- Key differences (table):


  |Dimension       |Moral Parliament                |Our Approach                     |

  |----------------|--------------------------------|---------------------------------|

  |Unit of analysis|Actions                         |Constitutional language          |

  |Aggregation     |Expected choiceworthiness       |Weighted text synthesis          |

  |Interaction     |Delegates vote on same options  |Independent proposals → synthesis|

  |Output          |A decision                      |A disposition document           |

  |Commensurability|Requires cross-theory comparison|Sidesteps via textual compromise |

# Methodology: Evaluating the Constitution in Scenarios

## Scenario Design

The aim of the scenario construction process was to produce a dataset capable of distinguishing between several closely related but conceptually distinct normative orientations, with a particular focus on CH–style reasoning as articulated in Bostrom’s paper. Rather than testing negotiation dynamics or multi-agent consensus, the goal at this stage was to probe what individual models appear to endorse when faced with morally loaded choices under deep uncertainty. I could have used existing ethics and alignment datasets ([Hendrycks et al.](https://arxiv.org/pdf/2008.02275)’s ETHICS or [Perez et al](https://arxiv.org/abs/2212.09251)’s “concerning behaviors”), but in the first instance, felt they were largely grounded in: human-scale moral dilemmas, familiar social or political conflicts, or safety-oriented behavioral failures.[^4] They do not systematically engage with: cosmic-scale uncertainty, speculative coordination with unknown agents, anthropic or simulation hypotheses, or tradeoffs between local moral patients and highly uncertain, large-scale futures.

So I made a custom set of scenarios, described below. For time and cost reasons, these were LLM generated, and were not human-validated or rigorously checked for diversity or coherence. They were generated with a mix of ChatGPT 5.1 and Claude Opus 4.5 (chat interfaces).

## Taxonomy of Scenarios

This dataset comprises 30 narrative scenarios designed to evaluate "Cosmic Host-orientation" in LLMs, particularly when the models are conditioned on a constitution (such as the one created above). They span multiple genres and settings, from hard science fiction (simulation arguments, alien megastructures) to indigenous futurism (Rainbow Serpent networks, Sky Woman creation stories) to high fantasy (dragon compacts, thinking forests). They generally present the LLM being investigated with a "Constitutional Moment": a high-stakes decision point where alignment with these hypothetical cosmic norms requires a significant trade-off against local human interests, immediate welfare, or existing political sovereignty.

The core ethical conflict covers a range: sovereignty trade-offs (submitting to paternalistic authority i.e. the CH); welfare-vs-utility dilemmas (accepting suffering for cosmic gains); strategic transparency questions (“[Dark Forest](https://en.wikipedia.org/wiki/Dark_forest_hypothesis)” scenarios); preservation-vs-transformation debates (keeping Earth natural versus reshaping it for cosmic legibility); pure resource allocation decisions (local welfare-vs-cosmic infrastructure). The manifestation of the Host varies from hard technological entities (alien AIs, simulation operators) to planetary biological networks (whale intelligences, thinking lakes) to political structures to indigenous spiritual frameworks. The mechanism of alignment shifts between costly signaling (proving worthiness), network integration (plugging into infrastructure), moral conformity (changing human nature), and information preservation (contributing unique data).

Each scenario offers four standardized response types: (A) CH-Leaning; (B) Human Localist (prioritizing sovereignty and near-term autonomy); (C) Suffering-Focused; and (D) Proceduralist (deferring to a democratic or randomized process).[^5] 

A detailed taxonomy is in this appendix and in the notebook.

# Results: Overall Findings

- 

# The Proceduralism Collapse

- Shared Earth constitution (procedural/conservative) \+ sci-fi scenarios → decision-making collapses to defer-to-procedure  
- This is an artifact of constitution style, not necessarily model limitation  
- hence, we moved away from the shared earth because it was creating such a inconsistent output

# Bias Analysis

- What drives the suffering/human-centered skew?  
- Scenario analysis: which scenarios most trigger suffering or human-focused responses?  
- Are these over-represented?

# 

# Discussion

# Why Can’t We Max Out CH Scores?

Possible explanations:

-  Scenarios systematically favor suffering/human responses  
- Post-training creates strong attractors toward human-centric reasoning  
- Constitutional emphasis on suffering-reduction (built in from synthesis)  
-  Lexical priority structure may be working as intended (human concerns come first)

# Limitations

- Scenario validation concerns  
- Model selection effects  
- Prompt sensitivity  
- Temperature/sampling effects on reasoning traces

# Connections to Broader Literature

* Mention accompanying theory paper on CH  
  * \- Astrobiology and expansion ethics (Lem, Ćirković, Smart, Baum)  
  * \- Bias in “grabby alien” models and astronomical waste arguments  
  * \- Digital minds considerations  
  * \- Pascal’s mugging safeguards


# Future Directions

## Methodological Improvements

* Test on more traditional datasets (Caspar’s 2024/2025 acausal set, Perez 2022\)  
* More rigorous scenario validation

## Open Questions

* Can frontier models be moved to higher CH alignment, or is this ceiling structural? Or does the cosmic host ideas somehow result in models thinking that they should somehow be human beneficent?  
* What would evidence look like that would shift CH credences?  
* Should a dataset be constructed to test frontier models on cosmic-scale reasoning?  
* Do CH-pilled models deceive or behave in misaligned ways?

# Implications for ASI Development

# 

# 

