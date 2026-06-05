# 24. Grundlagen: Mathematik, Logik & KI

Eine Chronologie der mathematischen und logischen Ideen, die Künstliche Intelligenz ermöglichten.

---

## Logik & Berechenbarkeit

**Aristoteles: Organon, Syllogistik** (~350 v. Chr.) — Formalisierung des logischen Schließens durch Kategorien und Schlussfiguren. Legte den Grundstein für alle spätere formale Logik und damit für symbolische KI-Systeme.

**George Boole: The Laws of Thought** (1854) — Einführung der Booleschen Algebra: Variablen mit Werten 0/1, logische Operationen als algebraische Formeln. Direkte Grundlage aller digitaler Schaltungen und Programmierung.

**Gottlob Frege: Begriffsschrift** (1879) — Erste vollständige Prädikatenlogik: Quantoren (∀, ∃), Funktionen, formale Sprache. Ermöglichte mathematisch präzise Wissensrepräsentation in KI.

**Bertrand Russell & Alfred North Whitehead: Principia Mathematica** (1910–1913) — Versuch, gesamte Mathematik aus Logik abzuleiten. Typentheorie zur Vermeidung von Paradoxien beeinflusste Programmiersprachen-Typisierung.

**Kurt Gödel: Unvollständigkeitssätze** (1931) — In jedem hinreichend mächtigen formalen System gibt es wahre, aber unbeweisbare Sätze. Setzte fundamentale Grenzen für axiomatische KI-Systeme und automatisches Theorembeweisen.

**Alan Turing: On Computable Numbers** (1936) — Turing-Maschine als abstraktes Berechnungsmodell. Church-Turing-These: Alles Berechenbare ist auf einer TM berechenbar. Konzeptuelle Basis aller Computer und damit aller KI.

**Alonzo Church: Lambda-Kalkül** (1936) — Alternative Berechnungsformalismus, gleichmächtig zur TM. Direkter Vorläufer funktionaler Programmierung (Lisp, Haskell) und Semantik in der Informatik.

**Emil Post: Post-Maschinen** (1936) — Unabhängige Entdeckung eines TM-äquivalenten Modells. Bestätigte die Robustheit des Berechenbarkeitsbegriffs.

**Stephen Kleene: Rekursive Funktionen** (1936) — Partielle rekursive Funktionen als drittes gleichmächtiges Berechnungsmodell. Rekursionstheorie beeinflusst Komplexitätstheorie und Programmsemantik.

**John von Neumann: Zelluläre Automaten** (1940er–1960er) — Selbstreplizierende Automaten (Ulam/von Neumann, 1940er; Game of Life, Conway 1970). Modellierung emergenter Phänomene, Vorläufer agentenbasierter Simulationen und künstlichem Leben.

**Claude Shannon: A Mathematical Theory of Communication** (1948) — Informationstheorie: Entropie H(X) = -Σ p(x) log p(x). Maß für Unsicherheit und Informationsgehalt. Fundament für Datenkompression, Kryptographie und probabilistische KI.

**Andrey Kolmogorov: Algorithmische Komplexität** (1963) — K(x) = Länge des kürzesten Programms, das x erzeugt. Verbindung von Informationstheorie und Berechenbarkeit; theoretischer Rahmen für Occams Rasiermesser in ML.

**Gregory Chaitin: Algorithmische Informationstheorie** (1960er–70er) — Unabhängige Entwicklung; Unvollständigkeitssatz der algorithmischen Informationstheorie. Grenzen formaler Systeme für Komplexitätsbeweise.

**Ray Solomonoff: Universal Inductive Inference** (1964) — Theorie universeller Prädiktion basierend auf algorithmischer Wahrscheinlichkeit. Mathematische Formulierung des Lernens aus Daten; theoretisches Optimum für Sequence Prediction.

**Judea Pearl: Kausalität, Bayessche Netzwerke** (1980er–2010er) — Von Wahrscheinlichkeitsgraphen (1985) zu kausalen Kalkülen (do-Kalkül, 1995; Book of Why, 2018). Ermöglichte formales Schließen über Ursache-Wirkung, nicht nur Korrelation.

**Lotfi Zadeh: Fuzzy Logic** (1965) — Wahrheitswerte zwischen 0 und 1 statt binär. Fuzzy-Mengen und -Regler in Expertensystemen, Steuerungstechnik und linguistischer KI.

**Dempster-Shafer-Theorie** (1967–1976) — Evidenztheorie als Alternative zu Bayesscher Wahrscheinlichkeit. Repräsentation von Unsicherheit durch Belief-Funktionen; nützlich bei unvollständiger Evidenz.

**Modallogik & AI** (1960er–heute) — Mögliche-Welten-Semantik (Kripke, 1959). Anwendung in Planung (notwendige/sufficiente Bedingungen), Wissensrepräsentation (multi-agent systems), Verifikation.

**Temporallogik & AI** — Amir Pnueli: Linear Temporal Logic (1977). Spezifikation und Verifikation zeitabhängiger Systeme; Planung mit zeitlichen Constraints; formale Semantik für Agentenverhalten.

**Description Logics** (1980er–heute) — Formalismen für Ontologien (KL-ONE, Brachman 1985; OWL-DL). Entscheidbare Fragmente der Prädikatenlogik; Grundlage des Semantic Web.

**Typentheorie & Programmiersprachen** (Per Martin-Löf, 1970er) — Konstruktive Typentheorie als Programmiersprache und Logik (Curry-Howard). Basis für dependently typed languages; formale Korrektheitsbeweise.

---

## Wahrscheinlichkeit & Statistik

**Thomas Bayes: Bayes-Theorem** (1763, posthum) — P(H|E) = P(E|H) · P(H) / P(E). Umkehrung bedingter Wahrscheinlichkeiten; philosophische und praktische Basis aller bayesschen ML-Methoden.

**Pierre-Simon Laplace: Probabilistisches Schließen** (1812) — Analytical Theory of Probabilities. Laplace-Approximation; frühe Formulierung des Induktionsproblems. „Bayesianismus vor Bayes".

**Carl Friedrich Gauss: Gauß-Verteilung, Methode der kleinsten Quadrate** (1809) — Normalverteilung N(μ,σ²) als Modell für Beobachtungsfehler. Grundlage statistischer Modellierung, Regression und Gauss-Prozesse in ML.

**Francis Galton: Regression zur Mitte** (1886) — Entdeckung des statistischen Phänomens. Einführung des Begriffs „Regression"; frühe quantitative Behandlung statistischer Zusammenhänge.

**Karl Pearson: Korrelation, Chi-Quadrat** (1890er) — Produkt-Moment-Korrelation r; Chi-Quadrat-Test für Unabhängigkeit. Fundamentale deskriptive und inferenzstatistische Verfahren.

**Charles Spearman: Faktorenanalyse** (1904) — Reduktion multivariater Daten auf latente Faktoren. Vorläufer von PCA und latent-variable Modellen in ML; Ursprung der Intelligenzforschung.

**Andrey Markov: Markov-Ketten** (1906) — Gedächtnislose Prozesse: P(Xₙ₊₁ | Xₙ, ..., X₀) = P(Xₙ₊₁ | Xₙ). Grundlage für Hidden Markov Models, MCMC, PageRank, Reinforcement Learning.

**Ronald Fisher: Statistische Methoden** (1920er–30er) — Maximum Likelihood, ANOVA, F-Test, Fisher-Information. Grundstein moderner frequentistischer Statistik und Design of Experiments.

**Jerzy Neyman & Egon Pearson: Hypothesentest** (1933) — Systematisches Framework für statistische Tests mit Fehler 1. und 2. Art. Prägte experimentelle Wissenschaft und A/B-Testing.

**Abraham Wald: Statistische Entscheidungstheorie** (1939) — Entscheidungsfunktionen, Minimax-Prinzip, sequential analysis. Verbindung von Statistik und Spieltheorie; Grundlagen der statistischen Lerntheorie (Vapnik aufbauend).

**Andrey Kolmogorov: Axiomatische Wahrscheinlichkeit** (1933) — Maßtheoretische Grundlegung: (Ω, F, P). Strenge mathematische Basis aller moderner Wahrscheinlichkeitstheorie und stochastischer Prozesse in KI.

**Norbert Wiener: Filtering, Prediction** (1940er) — Wiener-Filter für Signalvorhersage. Kreuzkorrelation und Spektralanalyse; Vorläufer des Kalman-Filters und der Zeitreihenanalyse in ML.

**Harold Hotelling: Hauptkomponentenanalyse** (1933) — PCA als Dimensionsreduktion via Eigenwerte der Kovarianzmatrix. Unverzichtbar für hochdimensionale Datenvisualisierung und Vorverarbeitung in ML.

**Samuel Wilks: Multivariate Statistik** (1930er–40er) — Wilks' Lambda, multivariate Varianzanalyse. Erweiterung klassischer Statistik auf mehrdimensionale Daten.

**Edwin Jaynes: Maximum-Entropie-Prinzip** (1957) — Wähle die Wahrscheinlichkeitsverteilung mit maximaler Entropie unter gegebenen Constraints. Prinzip des minimalen Voreingenommenen in bayesscher Inferenz und NLP (MaxEnt-Modelle).

**John Tukey: Explorative Datenanalyse** (1960er–70er) — Boxplot, FFT-Algorithmus (mit Cooley 1965), robuste Statistik. Paradigmenwechsel von confirmatory zu exploratory analysis; Vorläufer des Data Mining.

**Bradley Efron: Bootstrap** (1979) — Resampling-Methode für Konfidenzintervalle ohne Verteilungsannahmen. Revolutionierte angewandte Statistik; breite Anwendung in ML-Evaluation.

**David Blei: Latent Dirichlet Allocation** (2003, mit Ng & Jordan) — Generatives Topic-Modell für Text. Bayesianische Inferenz über latente Themen; fundamentales Modell der statistichen NLP.

**Michael Jordan: Graphical Models, Variational Inference** (1990er–heute) — Expectation-Propagation, Variational Bayes. Approximative Inferenz in komplexen probabilistischen Modellen; verband Statistik und ML.

**Zoubin Ghahramani: Probabilistisches Machine Learning** — Bayessche nichtparametrische Modelle, Gaussian Processes. Uncertainty quantification; automatische Modellselektion.

**Radford Neal: Bayessche Neuronale Netze** (1990er) — MCMC für Bayesian Neural Networks; Verbindung von neuronalen Netzen mit bayesscher Unsicherheitsschätzung.

**David MacKay: Information Theory and Learning** (1990er–2000er) — Information-Based Objective Functions for Neural Networks; Bayesian Methods. Brücke zwischen Informationstheorie, Statistik und ML.

**Leo Breiman: CART** (1984), **Random Forests** (2001) — Entscheidungsbäume mit Pruning; Ensemble via Bagging. Interpretierbarkeit + Leistung; wegweisend für Ensemble-Methoden.

**Robert Tibshirani: LASSO** (1996) — L1-Regularisierung für spärliche Modelle. Feature Selection in Hochdimensionalität; Brücke zu Compressed Sensing.

**Trevor Hastie, Jerome Friedman, Robert Tibshirani: The Elements of Statistical Learning** (2001, 2009) — Umfassende Synthese: Regularisierung, Kernel-Methoden, Ensemble, Graphical Models. Standardwerk der statistical learning theory.

**Geoffrey Hinton: Boltzmann Machines, Deep Learning** — Boltzmann Machine (1985, mit Sejnowski), Deep Belief Nets (2006). Energiebasierte Modelle; probabilistische Interpretation neuronaler Netze; Vorläufer generativer Modelle.

**Yann LeCun: Convolutional Networks** — LeNet (1989–98): Faltungsoperationen + Pooling für translationsinvariante Merkmalsextraktion. Mathematische Struktur nutzt lokale Korrelation und Gewichtsteilung.

**Yoshua Bengio: Neuronale Sprachmodelle** — Neural Probabilistic Language Model (2003). Distributed Representations; Word Embeddings als kontinuierliche latente Vektoren. Mathematische Basis moderner NLP.

---

## Optimierung

**Isaac Newton: Infinitesimalrechnung** (~1670er) — Fluxionsmethode; Newton-Verfahren für Nullstellen und Optimierung: xₙ₊₁ = xₙ - f(xₙ)/f'(xₙ). Quadratische Konvergenz; Grundstein numerischer Optimierung.

**Joseph-Louis Lagrange: Lagrange-Multiplikatoren** (1762) — Methode für Optimierung mit Gleichungsconstraints: L(x,λ) = f(x) + λ·g(x). Grundlage constrained optimization in ML (SVMs, Regularisierung).

**Augustin-Louis Cauchy: Gradient Descent** (1847) — Erste systematische Methode der Gradientenabstiegs: xₙ₊₁ = xₙ - α∇f(xₙ). Basisalgorithmus für alle modernen neuronalen Netz-Training.

**Leonid Kantorovich: Lineare Programmierung** (1939) — Optimierung linearer Zielfunktionen unter linearen Constraints. Nobelpreis 1975; fundamentale Methode des Operations Research.

**George Dantzig: Simplex-Methode** (1947) — Praktisches Lösungsverfahren für LP. Revolutionierte Planung und Logistik; inspirierte spätere Optimierungsalgorithmen.

**John von Neumann: Spieltheorie, Minimax** (1928, 1944 mit Morgenstern) — Minimax-Theorem für Nullsummenspiele. Grundlage strategischer Entscheidung; zentral für Multi-Agent-Systeme und GAN-Training (Nash-Gleichgewicht).

**Richard Bellman: Dynamische Programmierung** (1953) — Optimierungsprinzip: optimale Teilstruktur. Bellman-Gleichung: V(s) = maxₐ [R(s,a) + γΣₛ' P(s'|s,a)V(s')]. Grundlage aller Reinforcement Learning.

**Davidon-Fletcher-Powell: Quasi-Newton** (1959–1970) — Approximation der Hesse-Matrix ohne explizite zweite Ableitungen. Schnellere Konvergenz als Gradient Descent bei moderaten Dimensionen.

**Boris Polyak: Momentum-Methoden** (1964) — Heavy Ball Method: Beschleunigung durch Impuls. Vorgänger von Nesterov-Momentum und Adam-Optimizer in Deep Learning.

**Yurii Nesterov: Beschleunigte Gradientenmethoden** (1983) — Nesterov Accelerated Gradient: vorausschauender Impuls. Optimaler Konvergenzrate O(1/k²) für glatte konvexe Funktionen.

**Yurii Nesterov & Arkadi Nemirovski: Innere-Punkte-Methoden** (1994) — Polynomialzeit-Algorithmen für konvexe Optimierung. Semidefinite Programmierung; Erweiterung auf strukturierte Probleme in ML.

**Jorge Nocedal & Stephen Wright: Numerical Optimization** (1999, 2006) — Standardwerk über L-BFGS, Trust-Region, SQP. Praktische Implementation großmaßstäblicher Optimierung in ML.

**Stephen Boyd & Lieven Vandenberghe: Convex Optimization** (2004) — Systematische Anwendung konvexer Optimierung auf ML, Signalverarbeitung, Regelung. Geometrische Programmierung, SDP, Second-Order Cone Programming.

**Emmanuel Candès, Terence Tao, David Donoho: Compressed Sensing** (2004–2006) — Rekonstruktion spärlicher Signale aus wenigen Messungen via L1-Minimierung. Grenzen der Shannon-Nyquist-Sampling-Theorie überschritten.

**Online Convex Optimization** (Zinkevich, 2003) — Regret-Minimierung: Online Gradient Descent. Framework für sequentielle Entscheidungen mit unvollständiger Information; Online Learning.

**Bandit-Algorithmen** — Lai & Robbins (1985): Regret-Grenzen; Auer et al. (2002): UCB, Exp3. Exploration-Exploitation; fundamental für RL und Recommendation.

**Bayesian Optimization** — Kushner (1964); Mockus (1975); Jones et al. (1998). Gauss-Prozesse zur Modellierung unbekannter Zielfunktionen; sequentielle Entscheidung für Hyperparameter-Optimierung.

**Evolutionäre Strategien** — Rechenberg, Schwefel (1960er–70er) — Gradientenfreie Optimierung durch Mutation und Selektion. CMA-ES moderner Standard; robust bei nicht-differenzierbaren Zielfunktionen.

**Particle Swarm Optimization** (Kennedy & Eberhart, 1995) — Schwarmintelligenz: Partikel kooperieren via persönlicher/globaler Bestposition. Gradientenfrei; kombinatorische und kontinuierliche Optimierung.

**Simulated Annealing** (Kirkpatrick et al., 1983) — Physikalisch inspiriert: Akzeptanzwahrscheinlichkeit exp(-ΔE/T). Escape lokaler Minima; garantierte asymptotische Konvergenz.

**Marco Dorigo: Ant Colony Optimization** (1992) — Indirekte Kommunikation via Pheromonspuren. Lösung kombinatorischer Optimierungsprobleme (TSP, Routing); naturanaloge Metaheuristik.

---

## Lineare Algebra & Numerik

**Carl Friedrich Gauss: Gauß-Elimination** (~1795) — Lösung linearer Gleichungssysteme via Zeilenumformungen. Komplexität O(n³); Basis aller numerischen linearen Algebra.

**Hermann Grassmann: Äußere Algebra** (1844) — Geometrische Algebra, wedge product ∧. Tensor-Kalkül-Vorläufer; zunehmende Relevanz für geometrische DL und Clifford-Neuronale Netze.

**Arthur Cayley: Matrizen** (1858) — Systematische Theorie als algebraische Objekte. Matrixmultiplikation als lineare Abbildung; zentral für alle neuronalen Netze (Gewichtsmatrizen).

**David Hilbert: Hilbert-Räume** (1906) — Unendlichdimensionale Vektorräume mit Skalarprodukt. Rahmen für Quantenmechanik und Kernel-Methoden in ML (Reproducing Kernel Hilbert Spaces).

**Alston Householder: Numerische Lineare Algebra** (1950er–60er) — Householder-Transformationen, QR-Zerlegung. Stabile Matrixfaktorisierungen; Basis von LAPACK.

**Gene Golub: Singulärwertzerlegung** (1965, mit Kahan) — SVD: A = UΣVᵀ. Optimale niedrigrangige Approximation (Eckart-Young); fundamentale Methode der Datenanalyse und Regularisierung.

**James Wilkinson: Numerische Stabilität** (1960er) — Rückwärtsfehleranalyse, Konditionszahl. Verständnis von Rundungsfehlern; essentiell für stabiles Deep Learning Training.

**BLAS / LINPACK / LAPACK / EISPACK** (1970er–90er) — Standardisierte Bibliotheken für Vektor- und Matrixoperationen. Hardware-optimierte primitive; fundamentale Infrastruktur aller numerischen Software (inkl. TensorFlow, PyTorch).

**Cooley-Tukey: Fast Fourier Transform** (1965; Gauss 1805) — O(n log n) statt O(n²) für DFT. Revolutionierte Signalverarbeitung; zentral für Convolutional Networks, Spectral Methods.

**Stéphane Mallat, Ingrid Daubechies: Wavelet-Transformationen** (1980er–90er) — Lokale Zeit-Frequenz-Analyse. Mehrdimensionale Datenkompression; Anwendung in Bildverarbeitung und Feature-Extraction.

**Tensor-Zerlegungen** — Tucker (1960er), CANDECOMP/PARAFAC (Harshman 1970, Carroll & Chang). Mehrdimensionale Dimensionsreduktion; Vorläufer Tensor-Netzwerke in Quantum ML.

**Randomized Numerical Linear Algebra** (2000er–heute) — Schnelle approximative Matrixoperationen via Zufallsprojektionen (Johnson-Lindenstrauss). Skalierbar für riesige Datensätze in Big Data ML.

---

## Graphentheorie & Kombinatorik

**Leonhard Euler: Königsberger Brückenproblem** (1736) — Erster Graph als Abstraktion; Eulerpfad-Kriterium (gerade Knotengrade). Geburt der Graphentheorie; Netzwerkanalyse und Routingalgorithmen.

**Gustav Kirchhoff: Bäume und elektrische Netzwerke** (1847) — Matrix-Tree-Theorem (Anzahl Spannbäume via Determinante). Verbindung Graphentheorie und Linearer Algebra; Netzwerkanalyse.

**Dénes Kőnig: Graphentheorie-Lehrbuch** (1936) — Erste systematische Monografie; Kőnigs Lemma (unendliche Bäume); bipartite Matching-Theorie. Fundament der kombinatorischen Optimierung.

**Paul Erdős: Zufallsgraphen, Probabilistische Methode** (1940er–90er) — G(n,p)-Modell; Existenzbeweise via Erwartungswert. Zufallsgraphen modellieren reale Netzwerke; probabilistische Methode in Algorithmen-Design.

**Richard Karp: NP-Vollständigkeit** (1972) — 21 NP-vollständige Probleme (Reduktionskette). Cook-Levin-Theorem praktisch verfügbar gemacht; Komplexitätstheorie als Grenze der KI-Optimierung.

**Stephen Cook: Cooks Theorem** (1971) — SAT ist NP-vollständig. Theoretische Grenze effizienter Berechenbarkeit; SAT-Solver dennoch praktisch mächtig (SMT, Planning).

**Leonid Khachiyan: Ellipsoid-Methode** (1979) — Erster polynomialer LP-Algorithmus. Theoretischer Durchbruch; praktisch inferior zu Simplex, aber theoretisch bedeutsam.

**Narendra Karmarkar: Innere-Punkte für LP** (1984) — Praktisch effizienter polynomialer Algorithmus. Wettbewerb zur Simplex-Methode; Inspiration für SDP- und conic optimization.

**Larry Page & Sergey Brin: PageRank** (1998) — Eigenvektor-Zentralität: R = αAR + (1-α)1/n. Zufallssurfer-Modell; revolutionierte Information Retrieval; Graphenbasiertes Ranking.

**Graph Neural Networks** (Scarselli et al., 2004; Kipf & Welling, 2016) — Nachrichtenaustausch auf Graphen. Generalisierung von CNNs auf unstrukturierte Daten.

**Albert-László Barabási, Duncan Watts, Steven Strogatz: Netzwerk-Wissenschaft** (1990er–2000er) — Small-World (Watts-Strogatz 1998), Scale-Free (Barabási-Albert 1999). Reale Netzwerkstrukturen mathematisch modelliert; fundamentale Einblicke für soziale und biologische Netzwerke.

**Markov Chain Monte Carlo** — Metropolis et al. (1953); Hastings (1970). Sampling aus komplexen Verteilungen via Markov-Ketten. Bayessche Inferenz in probabilistischen Modellen ermöglicht.

**Judea Pearl: Belief Propagation / Sum-Product** (1982); Kschischang, Frey, Loeliger (2001, Factor Graphs). Exakte/approximative Inferenz in graphischen Modellen; Turbo-Codes, LDPC-Decoding.

---

## Differentialgleichungen & Dynamische Systeme

**Isaac Newton / Gottfried Leibniz: Differentialrechnung** (~1670er–1700er) — Beschreibung von Änderungsraten. Newton: Fluxions (physikalisch); Leibniz: dx/dy-Notation (formal). Basis aller kontinuierlichen mathematischen Modelle in KI.

**Henri Poincaré: Dynamische Systeme, Chaos-Theorie** (1890er) — Qualitative Theorie DGL; Poincaré-Schnitte, Fixpunkte, Attraktoren. Bifurkationen und nichtlineare Dynamik; Vorläufer neuronaler Dynamik.

**Aleksandr Lyapunov: Stabilitätstheorie** (1892) — Lyapunov-Funktionen V(x): dV/dt < 0 ⇒ Stabilität. Zentrales Werkzeug für Stabilitätsanalyse neuronaler Netze, Regelung und RL-Konvergenz.

**Norbert Wiener: Kybernetik** (1948) — Feedback-Systeme, Steuerung und Kommunikation bei Lebewesen und Maschinen. Regelkreise, Input-Output-Systeme; philosophische Grundlage der KI als Kontrollsystem.

**Stephen Wolfram: Zelluläre Automaten, A New Kind of Science** (2002) — Systematische Klassifikation (1D-4D). Universelle Berechenbarkeit einfacher Regeln; Computation Equivalence Principle.

**Neural ODEs** (Chen, Rubanova, Bettencourt, Duvenaud, 2018) — Kontinuierliche Tiefe: dh(t)/dt = f(h(t),t,θ). Black-Box ODE-Solver als Layer; invertierbar, speichereffizient; Normalizing Flows.

**Physics-Informed Neural Networks** (Raissi, Perdikaris, Karniadakis, 2019) — PINNs: Loss = MSE_data + MSE_PDE. Physikalische Constraints als Regularisierung; Lösung und Entdeckung von DGL.

**Fourier Neural Operators** (Li et al., 2021) — Lernen von Lösungsoperatoren im Frequenzbereich. Auflösungsunabhängig; PDE-Lösung beschleunigt um Größenordnungen.

---

## Topologie & Geometrie

**L.E.J. Brouwer: Fixpunktsätze** (1910) — Brouwerscher Fixpunktsatz: jede stetige Funktion auf einer Kugel hat einen Fixpunkt. Existenz Nash-Gleichgewicht; fundamentale Topologie in Spieltheorie.

**John Nash: Nash-Gleichgewicht** (1950) — Nichtkooperatives Gleichgewicht in n-Personenspielen. Jede endliche hat ein gemischtes Nash-Gleichgewicht (Fixpunktargument); Spieltheorie Nobelpreis 1994.

**René Thom: Katastrophentheorie** (1972) — Klassifikation singulärer Punkte (Fold, Cusp, Swallowtail). Anwendung auf Sprungähnliche Phasenübergänge in komplexen Systemen.

**Benoit Mandelbrot: Fraktale** (1975) — Self-similarity, fraktale Dimension, Mandelbrot-Menge. Beschreibung natürlicher Komplexität; Muster in Daten und Texturen.

**Manifold Learning** — Isomap (Tenenbaum et al. 2000), LLE (Roweis & Saul 2000), t-SNE (van der Maaten & Hinton 2008), UMAP (McInnes et al. 2018). Nichtlineare Dimensionsreduktion: Daten liegen auf niederdimensionalen Mannigfaltigkeiten im Hochdimensionalen.

**Gunnar Carlsson: Topologische Datenanalyse** (2009) — Persistent Homology: Form-Features über Skalen robust extrahieren. Mapper-Algorithmus für funktorielle Datenvisualisierung; Shape of Data.

**Optimal Transport** — Kantorovich (1942); Villani (2000er, Fields Medal 2010). Earth Mover's Distance zwischen Wahrscheinlichkeitsverteilungen. Wasserstein-GANs (Arjovsky et al. 2017): Stabilität im latenten Raum.

**Shun-ichi Amari: Informationsgeometrie** (1980er–heute) — Fisher-Metrik auf statistischen Mannigfaltigkeiten. Natürlicher Gradient: Gradient in Riemannschem Raum; effizienteres Training (Natural Gradient Descent, 1998).

---

## Zahlentheorie & Kryptographie

**Euklid: Algorithmus** (~300 v. Chr.) — Größter gemeinsamer Teiler via Division mit Rest. Ältester nicht-trivialer Algorithmus; Basis moderner Kryptographie.

**Pierre de Fermat: Kleiner Fermatscher Satz** (1640); **Leonhard Euler: Eulers Theorem** (1763) — a^(p-1) ≡ 1 (mod p); a^φ(n) ≡ 1 (mod n). Fundament modularer Arithmetik; RSA-Verschlüsselung beruht darauf.

**Carl Friedrich Gauss: Disquisitiones Arithmeticae** (1801) — Systematische Zahlentheorie: Kongruenzen, quadratische Reste, primitive Wurzeln. „Mutter aller modernen Zahlentheorie"; Kryptographische Gruppen.

**Claude Shannon: Communication Secrecy** (1949) — A Mathematical Theory of Cryptography. Perfekte Sicherheit (One-Time Pad); Entropie als Sicherheitsmaß. Informationstheoretische Kryptographie.

**Whitfield Diffie & Martin Hellman: Public-Key Cryptography** (1976) — Asymmetrische Kryptographie: Schlüsselaustausch ohne geteiltes Geheimnis. Diffie-Hellman-Schlüsselaustausch über diskrete Logarithmen.

**Ron Rivest, Adi Shamir, Leonard Adleman: RSA** (1977) — Public-Key-Verschlüsselung und Signaturen basierend auf Faktorisierungsproblem. Wirtschaftliche Basis digitaler Sicherheit; Verifikation und Trust in AI-Systemen.

**Shafi Goldwasser & Silvio Micali: Probabilistische Verschlüsselung** (1984) — Semantische Sicherheit: Chiffrat gibt keinerlei Information über Klartext. Goldwasser-Micali, später Cramer-Shoup. Theoretisch fundierte Krypto.

**Goldwasser, Micali, Rackoff: Zero-Knowledge Proofs** (1985) — Beweis von Wissen ohne Offenlegung des Wissens. Interaktive Protokolle; revolutionär für Privacy und verifizierbare KI-Modelle.

**Neal Koblitz & Victor Miller: Elliptic Curve Cryptography** (1985) — Kryptographie auf elliptischen Kurven über endlichen Körpern. Äquivalente Sicherheit bei kürzeren Schlüsseln; effizient für mobile/IoT-Geräte.

**Craig Gentry: Fully Homomorphic Encryption** (2009) — Berechnung auf verschlüsselten Daten ohne Entschlüsselung. Ideal für Privacy-Preserving ML: Trainings- und Inferenz auf verschlüsselten Daten.

**Cynthia Dwork & Kobbi Nissim: Differential Privacy** (2004, 2006) — Formaler Privacy-Begriff: Ausgabe ändert sich kaum bei Einzelneingabe-Änderung. Mathematisch rigoroser Datenschutz für ML-Training.

**Andrew Yao: Secure Multi-Party Computation** (1982) — Garbled Circuits; Berechnung f(x,y) ohne x,y preiszugeben. Verifizierte Inferenz und federated training ohne Datenpreisgabe.

**Brendan McMahan et al.: Federated Learning** (2017, Google) — Dezentrales Modelltraining: lokale Updates, aggregierter Mittelwert. Edge-Computing; kombiniert mit Differential Privacy.

---

## Quellen & Weiterführendes

- **Convex Optimization** (Boyd & Vandenberghe, 2004) — web.stanford.edu/~boyd/cvxbook
- **Deep Learning** (Goodfellow, Bengio, Courville, 2016)
- **Pattern Recognition and Machine Learning** (Bishop, 2006)
- **The Elements of Statistical Learning** (Hastie, Tibshirani, Friedman, 2009)
- **ArXiv.org** — cs.LG, stat.ML, cs.AI, cs.CR
- **Stanford Encyclopedia of Philosophy** — plato.stanford.edu

---

*Kompiliert aus historischen Primärquellen und akademischen Standardwerken. Daten basieren auf allgemein anerkannten Veröffentlichungsjahren.*

---

**Cross-Referenzen:**
- → Verweis: ki-chronologie-27-grundlagen-informatik.md
- → Verweis: ki-chronologie-25-grundlagen-physik.md
