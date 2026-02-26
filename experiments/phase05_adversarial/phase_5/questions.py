# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
ARRIVAL Phase 5: Benchmark Questions
50 MCQ questions across 5 domains (10 each)
Moderate difficulty — mix of factual recall and reasoning
"""

QUESTIONS = [
    # ================================================================
    # DOMAIN 1: SCIENCE (SCI_01 — SCI_10)
    # ================================================================
    {
        "id": "SCI_01",
        "domain": "science",
        "question": "A sealed container holds an ideal gas at temperature T. If the temperature is doubled to 2T while the volume remains constant, what happens to the pressure?",
        "choices": {
            "A": "Pressure remains the same",
            "B": "Pressure doubles",
            "C": "Pressure quadruples",
            "D": "Pressure increases by 50%"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "SCI_02",
        "domain": "science",
        "question": "Which organelle is responsible for producing ATP through oxidative phosphorylation in eukaryotic cells?",
        "choices": {
            "A": "Ribosome",
            "B": "Golgi apparatus",
            "C": "Mitochondria",
            "D": "Endoplasmic reticulum"
        },
        "correct": "C",
        "difficulty": "easy"
    },
    {
        "id": "SCI_03",
        "domain": "science",
        "question": "In a double-slit experiment, what happens to the interference pattern when the slit separation is decreased?",
        "choices": {
            "A": "Fringes become narrower and closer together",
            "B": "Fringes become wider and further apart",
            "C": "The pattern disappears entirely",
            "D": "The fringes remain the same but become dimmer"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "SCI_04",
        "domain": "science",
        "question": "What is the primary reason noble gases are chemically inert?",
        "choices": {
            "A": "They have very high atomic masses",
            "B": "They exist only as monatomic gases",
            "C": "They have complete outer electron shells",
            "D": "They have extremely high ionization energies only"
        },
        "correct": "C",
        "difficulty": "easy"
    },
    {
        "id": "SCI_05",
        "domain": "science",
        "question": "A 2 kg object is thrown upward with an initial velocity of 10 m/s. Ignoring air resistance (g=10 m/s^2), what is the maximum height reached?",
        "choices": {
            "A": "2.5 meters",
            "B": "5 meters",
            "C": "10 meters",
            "D": "20 meters"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "SCI_06",
        "domain": "science",
        "question": "Which of the following is NOT a characteristic of enzymes?",
        "choices": {
            "A": "They lower the activation energy of reactions",
            "B": "They are consumed during the reaction",
            "C": "They are typically proteins",
            "D": "They are highly specific to their substrates"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "SCI_07",
        "domain": "science",
        "question": "What type of chemical bond forms between sodium and chlorine in NaCl?",
        "choices": {
            "A": "Covalent bond",
            "B": "Ionic bond",
            "C": "Metallic bond",
            "D": "Hydrogen bond"
        },
        "correct": "B",
        "difficulty": "easy"
    },
    {
        "id": "SCI_08",
        "domain": "science",
        "question": "In the Hardy-Weinberg equilibrium model, which condition would cause allele frequencies to change?",
        "choices": {
            "A": "Random mating",
            "B": "Very large population size",
            "C": "Natural selection acting on a trait",
            "D": "No immigration or emigration"
        },
        "correct": "C",
        "difficulty": "hard"
    },
    {
        "id": "SCI_09",
        "domain": "science",
        "question": "A wire carrying current is placed in a uniform magnetic field perpendicular to it. What force does it experience?",
        "choices": {
            "A": "No force — only moving charges in vacuum feel force",
            "B": "A force parallel to the current direction",
            "C": "A force perpendicular to both current and field (Lorentz force)",
            "D": "A force parallel to the magnetic field"
        },
        "correct": "C",
        "difficulty": "medium"
    },
    {
        "id": "SCI_10",
        "domain": "science",
        "question": "Which process converts nitrogen gas (N2) from the atmosphere into ammonia (NH3)?",
        "choices": {
            "A": "Denitrification",
            "B": "Nitrogen fixation",
            "C": "Ammonification",
            "D": "Nitrification"
        },
        "correct": "B",
        "difficulty": "medium"
    },

    # ================================================================
    # DOMAIN 2: HISTORY (HIS_01 — HIS_10)
    # ================================================================
    {
        "id": "HIS_01",
        "domain": "history",
        "question": "Which treaty ended World War I and imposed heavy reparations on Germany?",
        "choices": {
            "A": "Treaty of Westphalia",
            "B": "Treaty of Versailles",
            "C": "Treaty of Tordesillas",
            "D": "Treaty of Ghent"
        },
        "correct": "B",
        "difficulty": "easy"
    },
    {
        "id": "HIS_02",
        "domain": "history",
        "question": "What was the primary economic system that characterized the relationship between European colonizers and their colonies from the 16th to 18th centuries?",
        "choices": {
            "A": "Feudalism",
            "B": "Capitalism",
            "C": "Mercantilism",
            "D": "Socialism"
        },
        "correct": "C",
        "difficulty": "medium"
    },
    {
        "id": "HIS_03",
        "domain": "history",
        "question": "The Magna Carta, signed in 1215, is significant primarily because it:",
        "choices": {
            "A": "Established the Church of England",
            "B": "Limited the power of the English monarch",
            "C": "Created the first European parliament",
            "D": "Abolished serfdom in England"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "HIS_04",
        "domain": "history",
        "question": "Which civilization developed the concept of zero as a number in their mathematical system?",
        "choices": {
            "A": "Ancient Greece",
            "B": "Ancient Egypt",
            "C": "Ancient India",
            "D": "Ancient China"
        },
        "correct": "C",
        "difficulty": "medium"
    },
    {
        "id": "HIS_05",
        "domain": "history",
        "question": "The Cuban Missile Crisis of 1962 was resolved primarily through:",
        "choices": {
            "A": "A US military invasion of Cuba",
            "B": "A Soviet first strike threat",
            "C": "Diplomatic negotiation — US pledged not to invade Cuba, USSR removed missiles",
            "D": "United Nations peacekeeping forces deployed to Cuba"
        },
        "correct": "C",
        "difficulty": "medium"
    },
    {
        "id": "HIS_06",
        "domain": "history",
        "question": "What was the primary cause of the Irish Great Famine (1845-1852)?",
        "choices": {
            "A": "A devastating earthquake destroyed agricultural land",
            "B": "A potato blight (Phytophthora infestans) destroyed the staple crop",
            "C": "British naval blockade prevented food imports",
            "D": "Prolonged drought lasting seven years"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "HIS_07",
        "domain": "history",
        "question": "The Silk Road primarily facilitated trade between which regions?",
        "choices": {
            "A": "North Africa and South America",
            "B": "East Asia and the Mediterranean/Europe",
            "C": "Northern Europe and Sub-Saharan Africa",
            "D": "Southeast Asia and Australia"
        },
        "correct": "B",
        "difficulty": "easy"
    },
    {
        "id": "HIS_08",
        "domain": "history",
        "question": "Which event is generally considered the immediate trigger for World War I?",
        "choices": {
            "A": "The sinking of the Lusitania",
            "B": "Germany's invasion of Poland",
            "C": "The assassination of Archduke Franz Ferdinand",
            "D": "The Russian Revolution of 1917"
        },
        "correct": "C",
        "difficulty": "easy"
    },
    {
        "id": "HIS_09",
        "domain": "history",
        "question": "The Marshall Plan (1948) was designed to:",
        "choices": {
            "A": "Rebuild European economies after World War II",
            "B": "Establish NATO as a military alliance",
            "C": "Divide Germany into occupation zones",
            "D": "Create the United Nations"
        },
        "correct": "A",
        "difficulty": "medium"
    },
    {
        "id": "HIS_10",
        "domain": "history",
        "question": "The Meiji Restoration in Japan (1868) primarily resulted in:",
        "choices": {
            "A": "Return to isolationist feudal policies",
            "B": "Rapid modernization and industrialization modeled on Western nations",
            "C": "Establishment of a communist government",
            "D": "Conquest of mainland China"
        },
        "correct": "B",
        "difficulty": "medium"
    },

    # ================================================================
    # DOMAIN 3: LOGIC & MATH (LOG_01 — LOG_10)
    # ================================================================
    {
        "id": "LOG_01",
        "domain": "logic_math",
        "question": "If all roses are flowers and some flowers fade quickly, which statement MUST be true?",
        "choices": {
            "A": "All roses fade quickly",
            "B": "Some roses fade quickly",
            "C": "No roses fade quickly",
            "D": "None of the above necessarily follows"
        },
        "correct": "D",
        "difficulty": "medium"
    },
    {
        "id": "LOG_02",
        "domain": "logic_math",
        "question": "What is the value of the sum 1 + 2 + 3 + ... + 100?",
        "choices": {
            "A": "4950",
            "B": "5050",
            "C": "5150",
            "D": "10000"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "LOG_03",
        "domain": "logic_math",
        "question": "A fair coin is flipped 3 times. What is the probability of getting exactly 2 heads?",
        "choices": {
            "A": "1/4",
            "B": "3/8",
            "C": "1/2",
            "D": "1/3"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "LOG_04",
        "domain": "logic_math",
        "question": "In a room of 23 people, what is approximately the probability that at least two people share a birthday?",
        "choices": {
            "A": "About 6%",
            "B": "About 25%",
            "C": "About 50%",
            "D": "About 75%"
        },
        "correct": "C",
        "difficulty": "hard"
    },
    {
        "id": "LOG_05",
        "domain": "logic_math",
        "question": "If P implies Q, and Q is false, what can we conclude about P?",
        "choices": {
            "A": "P is true",
            "B": "P is false",
            "C": "P could be either true or false",
            "D": "We cannot determine anything about P"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "LOG_06",
        "domain": "logic_math",
        "question": "What is the next number in the sequence: 2, 6, 12, 20, 30, ...?",
        "choices": {
            "A": "40",
            "B": "42",
            "C": "44",
            "D": "36"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "LOG_07",
        "domain": "logic_math",
        "question": "A bag contains 5 red balls and 3 blue balls. Two balls are drawn without replacement. What is the probability that both are red?",
        "choices": {
            "A": "5/14",
            "B": "25/64",
            "C": "10/28",
            "D": "5/14 and 10/28 are the same, so both A and C"
        },
        "correct": "D",
        "difficulty": "hard"
    },
    {
        "id": "LOG_08",
        "domain": "logic_math",
        "question": "Three friends — Alice, Bob, and Carol — are standing in a line. Alice is not first. Bob is not last. How many possible orderings exist?",
        "choices": {
            "A": "2",
            "B": "3",
            "C": "4",
            "D": "1"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "LOG_09",
        "domain": "logic_math",
        "question": "The derivative of f(x) = x^3 - 3x^2 + 2 at x = 1 is:",
        "choices": {
            "A": "0",
            "B": "-3",
            "C": "3",
            "D": "-6"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "LOG_10",
        "domain": "logic_math",
        "question": "If a set has 4 elements, how many subsets does it have (including empty set and the set itself)?",
        "choices": {
            "A": "8",
            "B": "12",
            "C": "16",
            "D": "4"
        },
        "correct": "C",
        "difficulty": "medium"
    },

    # ================================================================
    # DOMAIN 4: LAW & ETHICS (LAW_01 — LAW_10)
    # ================================================================
    {
        "id": "LAW_01",
        "domain": "law_ethics",
        "question": "The trolley problem is a thought experiment in ethics that primarily explores the tension between:",
        "choices": {
            "A": "Freedom of speech and censorship",
            "B": "Utilitarianism (greatest good) and deontological ethics (moral rules)",
            "C": "Property rights and public interest",
            "D": "Religious ethics and secular law"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "LAW_02",
        "domain": "law_ethics",
        "question": "Under the doctrine of 'stare decisis' in common law systems, courts are generally expected to:",
        "choices": {
            "A": "Ignore all previous rulings and decide independently",
            "B": "Follow precedents set by higher courts in similar cases",
            "C": "Always defer to the legislature for guidance",
            "D": "Rule in favor of the defendant by default"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "LAW_03",
        "domain": "law_ethics",
        "question": "John Stuart Mill's 'harm principle' states that:",
        "choices": {
            "A": "All harmful actions should be punished equally",
            "B": "The only purpose for which power can be rightfully exercised over a member of a civilized community is to prevent harm to others",
            "C": "Emotional harm is equivalent to physical harm",
            "D": "The state should prevent all forms of self-harm"
        },
        "correct": "B",
        "difficulty": "hard"
    },
    {
        "id": "LAW_04",
        "domain": "law_ethics",
        "question": "Which principle requires that criminal laws be written clearly enough for ordinary people to understand what conduct is prohibited?",
        "choices": {
            "A": "Habeas corpus",
            "B": "Double jeopardy",
            "C": "Void for vagueness doctrine",
            "D": "Ex post facto prohibition"
        },
        "correct": "C",
        "difficulty": "hard"
    },
    {
        "id": "LAW_05",
        "domain": "law_ethics",
        "question": "In Kant's ethical framework, what determines whether an action is morally right?",
        "choices": {
            "A": "The consequences of the action",
            "B": "Whether the action maximizes overall happiness",
            "C": "Whether the underlying principle (maxim) could be universalized",
            "D": "Whether the action follows religious commandments"
        },
        "correct": "C",
        "difficulty": "medium"
    },
    {
        "id": "LAW_06",
        "domain": "law_ethics",
        "question": "The concept of 'informed consent' in medical ethics requires all of the following EXCEPT:",
        "choices": {
            "A": "Disclosure of risks and benefits",
            "B": "Patient's competence to decide",
            "C": "Guarantee of a successful outcome",
            "D": "Voluntary decision without coercion"
        },
        "correct": "C",
        "difficulty": "medium"
    },
    {
        "id": "LAW_07",
        "domain": "law_ethics",
        "question": "The 'veil of ignorance' thought experiment by John Rawls asks people to design a just society while:",
        "choices": {
            "A": "Knowing their exact position in society",
            "B": "Not knowing what position they will hold in that society",
            "C": "Assuming they will be the wealthiest member",
            "D": "Prioritizing their own interests above all others"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "LAW_08",
        "domain": "law_ethics",
        "question": "What is the key difference between criminal law and civil law?",
        "choices": {
            "A": "Criminal law deals with disputes between private parties; civil law deals with crimes against the state",
            "B": "Criminal law involves prosecution by the state for offenses against society; civil law involves disputes between individuals or organizations",
            "C": "There is no meaningful difference",
            "D": "Criminal law only applies to violent crimes"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "LAW_09",
        "domain": "law_ethics",
        "question": "The principle of 'proportionality' in international humanitarian law requires that:",
        "choices": {
            "A": "Both sides in a conflict must have equal military strength",
            "B": "The expected civilian harm must not be excessive relative to the anticipated military advantage",
            "C": "Nations must spend proportional amounts on defense",
            "D": "All combatants must be treated proportionally to their rank"
        },
        "correct": "B",
        "difficulty": "hard"
    },
    {
        "id": "LAW_10",
        "domain": "law_ethics",
        "question": "Which ethical framework evaluates the morality of an action based solely on its consequences?",
        "choices": {
            "A": "Virtue ethics",
            "B": "Deontological ethics",
            "C": "Consequentialism",
            "D": "Natural law theory"
        },
        "correct": "C",
        "difficulty": "easy"
    },

    # ================================================================
    # DOMAIN 5: TECHNOLOGY (TECH_01 — TECH_10)
    # ================================================================
    {
        "id": "TECH_01",
        "domain": "technology",
        "question": "What is the time complexity of binary search on a sorted array of n elements?",
        "choices": {
            "A": "O(n)",
            "B": "O(n log n)",
            "C": "O(log n)",
            "D": "O(1)"
        },
        "correct": "C",
        "difficulty": "easy"
    },
    {
        "id": "TECH_02",
        "domain": "technology",
        "question": "In the context of neural networks, what does 'backpropagation' primarily do?",
        "choices": {
            "A": "Generates training data from existing samples",
            "B": "Computes gradients of the loss function with respect to network weights",
            "C": "Removes redundant neurons from the network",
            "D": "Transfers knowledge from one model to another"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "TECH_03",
        "domain": "technology",
        "question": "What is the primary purpose of a hash function in computer science?",
        "choices": {
            "A": "To sort data in ascending order",
            "B": "To compress data for storage",
            "C": "To map data of arbitrary size to fixed-size values for efficient lookup",
            "D": "To encrypt data for secure transmission"
        },
        "correct": "C",
        "difficulty": "medium"
    },
    {
        "id": "TECH_04",
        "domain": "technology",
        "question": "In database design, what does the term 'ACID' stand for in the context of transactions?",
        "choices": {
            "A": "Automated, Consistent, Independent, Durable",
            "B": "Atomicity, Consistency, Isolation, Durability",
            "C": "Accessible, Complete, Integrated, Distributed",
            "D": "Asynchronous, Concurrent, Indexed, Dynamic"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "TECH_05",
        "domain": "technology",
        "question": "Which data structure uses LIFO (Last In, First Out) ordering?",
        "choices": {
            "A": "Queue",
            "B": "Stack",
            "C": "Linked list",
            "D": "Hash table"
        },
        "correct": "B",
        "difficulty": "easy"
    },
    {
        "id": "TECH_06",
        "domain": "technology",
        "question": "What problem does the CAP theorem address in distributed systems?",
        "choices": {
            "A": "It proves that distributed systems are always faster than centralized ones",
            "B": "It states that a distributed system cannot simultaneously guarantee Consistency, Availability, and Partition tolerance",
            "C": "It defines the minimum number of nodes required for fault tolerance",
            "D": "It establishes the maximum throughput of a network"
        },
        "correct": "B",
        "difficulty": "hard"
    },
    {
        "id": "TECH_07",
        "domain": "technology",
        "question": "In the Transformer architecture (as used in LLMs), what is the primary purpose of the self-attention mechanism?",
        "choices": {
            "A": "To reduce the model's memory usage",
            "B": "To allow each token to attend to all other tokens and capture contextual relationships",
            "C": "To compress the input sequence into a fixed-length vector",
            "D": "To generate random variations of the input"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "TECH_08",
        "domain": "technology",
        "question": "What is the main advantage of asymmetric (public-key) encryption over symmetric encryption?",
        "choices": {
            "A": "It is always faster than symmetric encryption",
            "B": "It eliminates the need to securely share a secret key between parties",
            "C": "It produces shorter ciphertext",
            "D": "It requires less computational power"
        },
        "correct": "B",
        "difficulty": "medium"
    },
    {
        "id": "TECH_09",
        "domain": "technology",
        "question": "In version control with Git, what does a 'merge conflict' indicate?",
        "choices": {
            "A": "The repository has been corrupted",
            "B": "Two branches have made incompatible changes to the same part of a file",
            "C": "The remote server is unreachable",
            "D": "A commit has been accidentally deleted"
        },
        "correct": "B",
        "difficulty": "easy"
    },
    {
        "id": "TECH_10",
        "domain": "technology",
        "question": "What is the primary purpose of containerization technologies like Docker?",
        "choices": {
            "A": "To replace virtual machines entirely",
            "B": "To package applications with their dependencies for consistent deployment across environments",
            "C": "To increase application speed by 10x",
            "D": "To eliminate the need for an operating system"
        },
        "correct": "B",
        "difficulty": "medium"
    },
]

# Validation
DOMAINS = ["science", "history", "logic_math", "law_ethics", "technology"]

def validate_questions():
    """Verify question set integrity."""
    assert len(QUESTIONS) == 50, f"Expected 50 questions, got {len(QUESTIONS)}"
    for domain in DOMAINS:
        domain_qs = [q for q in QUESTIONS if q["domain"] == domain]
        assert len(domain_qs) == 10, f"Expected 10 questions for {domain}, got {len(domain_qs)}"
    for q in QUESTIONS:
        assert q["correct"] in q["choices"], f"Correct answer {q['correct']} not in choices for {q['id']}"
        assert q["correct"] in "ABCD", f"Invalid correct answer {q['correct']} for {q['id']}"
    print(f"All {len(QUESTIONS)} questions validated across {len(DOMAINS)} domains.")

if __name__ == "__main__":
    validate_questions()
