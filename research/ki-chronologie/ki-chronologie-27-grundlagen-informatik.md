## 27. Grundlagen: Informatik, Programmierung & KI

Die technologischen Voraussetzungen für moderne KI: von Algorithmen und Programmiersprachen über Betriebssysteme, Datenbanken und Netzwerke bis hin zu spezialisierten Werkzeugen für maschinelles Lernen.

### Algorithmen & Datenstrukturen

- **Al-Khwarizmi: Algebra und Algorithmen** (~820 CE) — Muhammad ibn Musa al-Khwarizmi formalisierte systematische Lösungsverfahren für Gleichungen; der Begriff "Algorithmus" leitet sich von seinem Namen ab. Quelle: [Britannica](https://www.britannica.com/biography/al-Khwarizmi)
- **Ada Lovelace: Erster Algorithmus** (1843) — Augusta Ada King, Countess of Lovelace, beschrieb den ersten Algorithmus für Charles Babbages Analytical Engine, gilt als erste Programmiererin. Quelle: [Computer History Museum](https://www.computerhistory.org/timeline/computers/)
- **Alan Turing: Turing-Maschine** (1936) — Alan Turing formalisierte Berechenbarkeit und legte die theoretischen Grundlagen für alle nachfolgenden Computer. Quelle: [Stanford Encyclopedia of Philosophy](https://plato.stanford.edu/entries/turing/)
- **Alonzo Church: Lambda-Kalkül** (1936) — Entwickelte eine alternative Formalisierung von Berechenbarkeit; Grundlage funktionaler Programmierung und Typtheorie. Quelle: [Stanford Encyclopedia of Philosophy](https://plato.stanford.edu/entries/church/)
- **Donald Knuth: The Art of Computer Programming** (1968-heute) — Umfassendes Werk über Algorithmen und Datenstrukturen; fundamentale Referenz für effiziente Berechnung. Quelle: [Knuth's Website](https://www-cs-faculty.stanford.edu/~knuth/taocp.html)
- **Edsger Dijkstra: Kürzeste-Pfade-Algorithmus** (1959) — Graphalgorithmus essenziell für Routing, Planung und Netzwerkanalyse in KI-Systemen. Quelle: [CACM 1959](https://dl.acm.org/doi/10.1145/368993.368996)
- **Tony Hoare: Quicksort & Hoare-Logik** (Quicksort 1959, Hoare-Logik 1969) — Effizienter Sortieralgorithmus und formales System zur Verifikation von Programmkorrektheit. Quelle: [CACM 1961](https://dl.acm.org/doi/10.1145/366622.366647), [CACM 1969](https://dl.acm.org/doi/10.1145/363235.363259)

### Programmiersprachen für KI

- **John McCarthy: LISP** (1958) — Symbolische Programmiersprache dominierte KI-Forschung für Jahrzehnte; Basis für funktionale Programmierung. Quelle: [History of LISP](http://www-formal.stanford.edu/jmc/history/lisp/lisp.html)
- **Prolog** (1972) — Logische Programmiersprache für wissensbasierte Systeme und automatische Schlussfolgerung. Quelle: [Prolog History](https://www.iso.org/standard/21413.html)
- **Python** (1991) — Guido van Rossum; durch Einfachheit und umfangreiche Bibliotheken zur dominierenden KI-Sprache geworden. Quelle: [Python.org](https://www.python.org/doc/essays/cp4e/)
- **Julia** (2012) — Hochleistungssprache für wissenschaftliches Rechnen mit GPU-Support und differentiierbarer Programmierung. Quelle: [JuliaLang.org](https://julialang.org/)
- **NumPy** (Travis Oliphant, 2006) — Fundamentales Array-Computing für Python; Basis fast aller ML-Bibliotheken. Quelle: [Nature 2020](https://www.nature.com/articles/s41586-020-2649-2)
- **Pandas** (Wes McKinney, 2008) — Datenmanipulation und -analyse; unverzichtbar für ML-Datenaufbereitung. Quelle: [Pandas PyData](https://pandas.pydata.org/about/)
- **scikit-learn** (2010) — Umfassende ML-Bibliothek für klassische Algorithmen in Python. Quelle: [JMLR 2011](https://jmlr.org/papers/v12/pedregosa11a.html)
- **TensorFlow** (Google, 2015) — Open-Source-Framework für Deep Learning mit breiter Produktionsunterstützung. Quelle: [OSDI 2016](https://www.usenix.org/system/files/conference/osdi16/osdi16-abadi.pdf)
- **PyTorch** (Facebook/Meta, 2016) — Dynamisches Deep-Learning-Framework; bevorzugt in Forschung durch Pythonic-API. Quelle: [NeurIPS 2019](https://papers.neurips.cc/paper/2019/hash/bdbca288fee7f92f2bfa9f7012727740-Abstract.html)
- **JAX** (Google, 2018) — Funktionaler Ansatz für beschleunigtes numerisches Rechnen mit automatischer Differenzierung und JIT-Kompilierung. Quelle: [JAX ReadTheDocs](https://jax.readthedocs.io/)
- **Keras** (François Chollet, 2015) — Benutzerfreundliche High-Level-API für Deep Learning; später in TensorFlow integriert. Quelle: [Keras.io](https://keras.io/)
- **ONNX** (Microsoft/Facebook, 2017) — Offenes Format für ML-Modelle zur plattformübergreifenden Interoperabilität. Quelle: [ONNX.ai](https://onnx.ai/)
- **Mojo** (Modular, 2023) — Superset von Python mit C++-Performance; entwickelt für KI-Infrastruktur. Quelle: [Modular.com](https://www.modular.com/mojo)

### Betriebssysteme & Systemsoftware

- **UNIX** (Thompson & Ritchie, Bell Labs, 1969) — Mehrbenutzer-Betriebssystem; philosophische Grundlage moderner Systeme. Quelle: [Bell Labs](https://www.bell-labs.com/usr/dmr/www/hist.html)
- **Linux** (Linus Torvalds, 1991) — Open-Source-Kernel; dominierend in Servern, Cloud und KI-Infrastruktur. Quelle: [Linux Foundation](https://www.linuxfoundation.org/)
- **GNU Project** (Richard Stallman, 1983) — Freie Software-Bewegung; essenzielle Werkzeuge (GCC, GDB, Emacs). Quelle: [GNU.org](https://www.gnu.org/gnu/thegnuproject.html)
- **Docker** (2013) — Containerisierung vereinfachte Bereitstellung und Skalierung von KI-Anwendungen massiv. Quelle: [Docker.com](https://www.docker.com/)
- **Kubernetes** (Google, 2014) — Orchestrierung containerisierter Workloads; De-facto-Standard für ML-Ops. Quelle: [Kubernetes.io](https://kubernetes.io/)
- **Serverless Computing** (AWS Lambda, 2014) — Ereignisgesteuerte Ausführung ohne Servermanagement; vereinfachte KI-Inferenz-Skalierung. Quelle: [AWS Lambda](https://aws.amazon.com/lambda/)

### Datenbanken & Informationssysteme

- **Edgar Codd: Relational Model** (1970) — Mathematische Grundlage für relationale Datenbanken; fundamentale Datenorganisation. Quelle: [CACM 1970](https://dl.acm.org/doi/10.1145/362384.362685)
- **SQL Implementation** (IBM System R, 1974-79) — Erste praktische Umsetzung des relationalen Modells. Quelle: [IBM Research](https://research.ibm.com/)
- **MySQL** (1995) — Weitverbreitete Open-Source-Datenbank für Web- und KI-Anwendungen. Quelle: [MySQL.com](https://www.mysql.com/)
- **PostgreSQL** (1996) — Fortgeschrittene Open-Source-Datenbank mit JSON-Support und Erweiterbarkeit. Quelle: [PostgreSQL.org](https://www.postgresql.org/)
- **MongoDB** (2009) — Dokumentenorientierte NoSQL-Datenbank für flexible Datenmodelle in ML-Pipelines. Quelle: [MongoDB.com](https://www.mongodb.com/)
- **Hadoop** (2006) — Framework für verteilte Speicherung und Verarbeitung großer Datensätze (MapReduce). Quelle: [Apache Hadoop](https://hadoop.apache.org/)
- **Spark** (2009) — In-Memory-Verarbeitung für Big Data; MLlib für verteiltes maschinelles Lernen. Quelle: [Apache Spark](https://spark.apache.org/)
- **Vector Databases** (Pinecone, Weaviate, Milvus, Qdrant, 2019-heute) — Speicherung und effiziente Suche hochdimensionaler Vektoren für Embeddings und RAG. Quelle: [Pinecone.io](https://www.pinecone.io/), [Weaviate.io](https://weaviate.io/)
- **Lakehouse Architecture** (Databricks, 2020) — Vereint Data Lakes und Data Warehouses; optimiert für ML-Workloads. Quelle: [CIDR 2021](https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf)

### Netzwerke & Verteilte Systeme

- **ARPANET** (1969) — Erstes Paketvermittelndes Netzwerk; Vorläufer des Internets. Quelle: [Internet Society](https://www.internetsociety.org/internet/history-internet/)
- **TCP/IP** (1974) — Vinton Cerf und Bob Kahn; Protokollfamilie für zuverlässige Datenübertragung. Quelle: [IEEE Trans. Comm. 1974](https://ieeexplore.ieee.org/document/1094842)
- **World Wide Web** (Tim Berners-Lee, CERN, 1989) — Hypertext-System; revolutionierte Informationszugang und Datenerfassung. Quelle: [W3C](https://www.w3.org/History/1989/proposal.html)
- **REST** (Roy Fielding, 2000) — Architekturstil für verteilte Systeme; Grundlage moderner APIs und Microservices. Quelle: [Fielding Dissertation](https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)
- **Bitcoin** (Satoshi Nakamoto, 2009) — Dezentrales Konsensprotokoll; Einfluss auf dezentrales Lernen und Vertrauen. Quelle: [Bitcoin Whitepaper](https://bitcoin.org/bitcoin.pdf)
- **Paxos** (Leslie Lamport, 1989) — Konsensalgorithmus für verteilte Systeme unter Fehlern. Quelle: [ACM TOCS 1998](https://dl.acm.org/doi/10.1145/279227.279229)
- **Raft** (Diego Ongaro & John Ousterhout, 2014) — Verständlicherer Konsensalgorithmus; weit verbreitet in verteilten Datenbanken. Quelle: [ATC 2014](https://www.usenix.org/system/files/conference/atc14/atc14-paper-ongaro.pdf)
- **Byzantine Fault Tolerance** (Castro & Liskov, 1999) — Konsens trotz böswilliger Knoten; relevant für dezentrales ML. Quelle: [OSDI 1999](https://pmg.csail.mit.edu/papers/osdi99.pdf)
- **Apache Kafka** (LinkedIn, 2011) — Verteilte Event-Streaming-Plattform für Echtzeit-Datenpipelines. Quelle: [Apache Kafka](https://kafka.apache.org/)
- **Microservices Architecture** — Entkopplung monolithischer Systeme; ermöglicht unabhängige Skalierung von ML-Services.

### Compiler & Laufzeitumgebungen

- **Grace Hopper: A-0 System** (1952) — Erster Compiler; ermöglichte symbolische Programmierung statt Maschinencode. Quelle: [CHM Grace Hopper](https://www.computerhistory.org/fellowawards/hall/grace-murray-hopper/)
- **FORTRAN** (John Backus, IBM, 1957) — Erste höhere Programmiersprache; numerische Berechnungen bis heute relevant. Quelle: [IBM Archives](https://www.ibm.com/ibm/history/ibm100/us/en/icons/fortran/)
- **Java HotSpot JVM** (Sun Microsystems, 1999) — JIT-Kompilierung für portierbare Hochleistungsanwendungen. Quelle: [Oracle JVM](https://www.oracle.com/java/technologies/)
- **V8 Engine** (Google, 2008) — Hochleistungs-JavaScript-Runtime mit JIT; Basis für Node.js und Web-ML. Quelle: [V8.dev](https://v8.dev/)
- **PyPy** (2007) — JIT-kompilierte Python-Implementierung; beschleunigt ML-Prototyping. Quelle: [PyPy.org](https://www.pypy.org/)
- **LLVM** (Chris Lattner, 2003) — Modularer Compiler-Framework; Basis für MLIR und TensorFlow-XLA. Quelle: [LLVM.org](https://llvm.org/)
- **Hindley-Milner Type Inference** — Statische Typsysteme für funktionale Sprachen; formale Korrektheit. Quelle: [J. Functional Programming](https://www.cambridge.org/core/journals/journal-of-functional-programming)
- **Formale Verifikation** — Hoare-Logik (1969), Model Checking (Clarke, Emerson, Sifakis, 1981), SAT/SMT-Solver, interaktive Beweiser (Coq, Isabelle, Lean), CompCert (2006), seL4 (2009). Quelle: [ACM Turing Award 2007](https://amturing.acm.org/award_winners/clarke_1167964.cfm)

### Sicherheit & Kryptographie (KI-spezifisch)

- **Adversarial Examples** (Szegedy et al., 2013; Goodfellow et al., 2014) — Fast unmerkliche Störungen führen zu Fehlklassifikationen; zentrales KI-Sicherheitsproblem. Quelle: [ICLR 2014](https://arxiv.org/abs/1312.6199), [ICLR 2015](https://arxiv.org/abs/1412.6572)
- **Differential Privacy** (Implementierungen: Google RAPPOR 2014, Apple 2016) — Mathematische Privatheitsgarantien für ML-Training mit sensiblen Daten. Quelle: [Google RAPPOR](https://arxiv.org/abs/1407.6981), [Apple](https://www.apple.com/privacy/docs/Differential_Privacy_Overview.pdf)
- **Federated Learning Security** — Dezentrales Training ohne Datenzentralisierung; Schutz vor Datenexfiltration bei gleichzeitiger Abwehr von Angriffen.
- **Model Inversion Attacks** — Rekonstruktion von Trainingsdaten aus Modellparametern. Quelle: [CCS 2015](https://dl.acm.org/doi/10.1145/2810103.2813677)
- **Membership Inference Attacks** — Bestimmung, ob ein Datensatz im Training verwendet wurde. Quelle: [IEEE S&P 2017](https://ieeexplore.ieee.org/document/7958568)
- **Poisoning Attacks** — Manipulation von Trainingsdaten zur Einbettung von Hintertüren. Quelle: [Big Data 2018](https://ieeexplore.ieee.org/document/8634958)
- **AI Red Teaming** — Systematisches Testen von KI-Systemen auf Sicherheitslücken und schädliche Outputs.

### Software Engineering für KI

- **MLflow** (Databricks, 2018) — Open-Source-Plattform für den gesamten ML-Lebenszyklus. Quelle: [MLflow.org](https://mlflow.org/)
- **Kubeflow** (Google, 2018) — ML-Workflow-Orchestrierung auf Kubernetes. Quelle: [Kubeflow.org](https://www.kubeflow.org/)
- **Weights & Biases** (2017) — Experiment Tracking und Visualisierung für ML-Teams. Quelle: [Wandb.ai](https://wandb.ai/)
- **Feast** (Tecton/Google, 2019) — Open-Source-Feature-Store für ML. Quelle: [Feast.dev](https://feast.dev/)
- **Tecton** (2018) — Feature-Store-Plattform für Operationalisierung von ML. Quelle: [Tecton.ai](https://www.tecton.ai/)
- **Fiddler** (2018) — Modell-Monitoring und Erklärbarkeit. Quelle: [Fiddler.ai](https://www.fiddler.ai/)
- **Arize** (2020) — Observability-Plattform für ML im Produktivbetrieb. Quelle: [Arize.com](https://arize.com/)
- **TensorFlow Serving** (Google, 2016) — Hochleistungs-Serving-System für ML-Modelle. Quelle: [TensorFlow Serving](https://www.tensorflow.org/tfx/guide/serving)
- **TorchServe** (AWS/PyTorch, 2020) — Flexibles Serving für PyTorch-Modelle. Quelle: [PyTorch Serve](https://pytorch.org/serve/)
- **NVIDIA Triton** (2018) — Inference-Server für GPUs mit Multi-Framework-Support. Quelle: [NVIDIA Triton](https://developer.nvidia.com/triton-inference-server)
- **Knowledge Distillation** (Hinton et al., 2015) — Komprimierung großer Modelle durch Übertragung auf kleinere. Quelle: [NeurIPS 2015](https://arxiv.org/abs/1503.02531)
- **Neural Architecture Search** — Automatisierte Optimierung von Netzwerkarchitekturen. Quelle: [Zoph & Le, ICLR 2017](https://arxiv.org/abs/1611.01578)
- **TensorFlow Lite** (Google, 2017) — Optimisierte Runtime für Edge- und Mobile-Geräte. Quelle: [TensorFlow Lite](https://www.tensorflow.org/lite)
- **ONNX Runtime** — Hochleistungs-Inferenz-Engine für ONNX-Modelle. Quelle: [ONNX Runtime](https://onnxruntime.ai/)
- **Core ML** (Apple) — Framework für ML-Inferenz auf Apple-Geräten. Quelle: [Apple Core ML](https://developer.apple.com/machine-learning/core-ml/)
- **OpenVINO** (Intel) — Toolkit für Optimierung und Bereitstellung auf Intel-Hardware. Quelle: [Intel OpenVINO](https://www.intel.com/content/www/us/en/developer/tools/openvino-toolkit.html)
- **TensorRT** (NVIDIA) — Hochoptimierte Inferenz für NVIDIA-GPUs. Quelle: [NVIDIA TensorRT](https://developer.nvidia.com/tensorrt)

---

**Cross-Referenzen:**
- → Verweis: ki-chronologie-24-grundlagen-mathematik.md
- → Verweis: ki-chronologie-34-kommunikation.md
