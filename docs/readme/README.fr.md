# DNA Workbench Suite

**Fichiers ADN, dossiers familiaux et flux de recherche dans un seul espace de travail local.**

[Télécharger](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Site Web](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=fr) · [Guide d'installation](../GETTING_STARTED.md) · [Traductions](#translations)

Organisez vos sources par personne et par fournisseur, comparez les fichiers compatibles et conservez les entrées et les résultats derrière chaque analyse.

![Visite guidée de l'application avec les modes clair et sombre, le sélecteur de langue et les fichiers de profil synthétiques](../images/workspace-demo.gif)

[Regardez la visite guidée de l'application](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=fr#tour) · [Galerie de captures d'écran](../GALLERY.md)

## Ce que tu peux faire

- Importez des fichiers ADN, des dossiers et des archives prises en charge. Vérifiez le fournisseur, le format et la version de référence avant de copier ou de déplacer quoi que ce soit.
- Regroupez les ensembles de données, les documents et les résultats par profil. Enregistrez l'origine de chaque fichier. Gardez les mesures directes séparées des valeurs déduites et notez quand des variantes ont été attribuées aux copies de chromosomes.
- Vérifiez la qualité des échantillons et comparez les sources. Créez un BestDataset versionné pour les flux de travail pouvant utiliser la même version de référence.
- Explorez les variantes et les fichiers de séquence avec les visualiseurs de génome. Comparez les profils ADN et reliez les notes de recherche aux dossiers familiaux et aux fichiers GEDCOM.
- Enregistrez les résultats avec leurs entrées et leurs journaux. Exportez des rapports et sauvegardez des profils pour une utilisation ultérieure.
- Utilisez l'assistant local en option pour naviguer dans l'espace de travail. Vous pouvez configurer l'IA externe séparément.

[Catalogue complet des fonctionnalités](../FEATURES.md) · [Formats pris en charge](../TOOL_FORMATS.md)

## Les outils et ce qu'ils font

Il s'agit d'outils sélectionnés que la suite intègre ou peut lancer. La disponibilité varie selon le flux de travail et le système d'exploitation. Certains modules et données de référence sont des téléchargements distincts.

| Outil | Ce que ça fait |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Lit, indexe et inspecte les fichiers de séquençage alignés aux formats SAM, BAM et CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Filtre, normalise, combine et inspecte les fichiers de variantes aux formats VCF et BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Vérifie la qualité de lecture du FASTQ et peut découper ou filtrer les lectures. |
| [mosdepth](https://github.com/brentp/mosdepth) | Mesure la couverture de lecture à partir des fichiers BAM et CRAM. |
| [MultiQC](https://seqera.io/multiqc/) | Combine les rapports de plusieurs outils de contrôle qualité en une seule vue. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Fonctionne avec les données de génotype pour des tâches telles que le filtrage des variantes, la parenté et l'analyse des composantes principales. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Utilise les données génotypiques pour déduire quelles variantes se trouvent sur la même copie d'un chromosome. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Recherche les segments d'ADN correspondants hérités d'un ancêtre commun. Il utilise des données génotypiques avec des variantes attribuées aux copies de chromosomes. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Utilise des lectures de séquençage pour attribuer des variantes aux copies de chromosomes. |
| [Truvari](https://github.com/ACEnglish/truvari) | Compare les variantes structurelles dans les fichiers VCF. |
| [IGV](https://igv.org/doc/desktop/) | Affiche les lectures alignées, les variantes et autres pistes du génome à des emplacements spécifiques. |
| [JBrowse](https://jbrowse.org/jb2/) | Vous permet de parcourir les séquences de référence et les pistes liées de manière interactive. |
| [GenomeSpy](https://genomespy.app/) | Restitue des graphiques génomiques interactifs avec l'accélération graphique du navigateur. |
| [Gramps](https://www.gramps-project.org/) | Organise les dossiers généalogiques, les arbres généalogiques et les données GEDCOM. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Annote les variantes à l’aide de sources et d’annotateurs sélectionnables. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Prédit comment les variantes peuvent affecter les gènes, les transcrits et les protéines. |
| [PharmCAT](https://pharmcat.org/) | Produit des rapports de recherche pharmacogénétique à partir des entrées de génotype prises en charge. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Exécute le modèle de langue locale facultatif sur des environnements d’exécution CPU et GPU compatibles. |

[Versions d'outils et prérequis](../VERSIONS.md)

## Commencez

Choisissez le package qui correspond à votre système d'exploitation et à votre processeur. La page de version répertorie les téléchargements x64 et ARM64 pour Windows, Linux et macOS. Certaines versions sont des aperçus.

1. Sur Windows, extrayez l'archive et exécutez le lanceur. Terminez la configuration de Core lorsque vous y êtes invité.
2. Sur Linux, démarrez le lanceur de shell inclus avec Python, GTK et WebKitGTK installés.
3. Sur macOS, conservez l'application à côté des fichiers d'espace de travail extraits. L'aperçu nécessite macOS 13 ou version ultérieure et Python 3.12 ou version ultérieure.
4. Commencez avec les échantillons synthétiques inclus pour essayer les flux de travail sans utiliser de fichiers personnels.

[Télécharger](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Guide d'installation](../GETTING_STARTED.md)

## Ligne de commande et automatisation

Utilisez le même registre de commandes via l'interface de bureau, CLI, JSON-RPC et MCP. Le service sans tête s'exécute sur la machine locale. Vous pouvez lister les commandes et lire leurs schémas sans ouvrir une fenêtre de bureau.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

L'assistant facultatif peut vous aider à parcourir les résultats. Ses réponses ne remplacent pas les données sources ni une analyse vérifiée.

> Logiciel de recherche. Les résultats dépendent de la contribution, de la méthode et des références. DNA Workbench Suite ne fournit pas de diagnostic clinique.

## Projet et accompagnement

Maintenu par Oktay Du / OD avec l'aide de l'IA.

[Confidentialité](../PRIVACY.md) · [Sécurité](../../SECURITY.md) · [Licence de projet](../../LICENSE) · [Signaler un problème](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Soutenir le projet · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Traductions

L'application comprend 36 langues d'interface hors ligne. Choisissez une traduction de cette page de projet ci-dessous.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
