import streamlit as st

# ==========================================
#        IDENTITÉ DE L'APPLICATION
# ==========================================

APP_NAME = "Grand Paname"
APP_VERSION = "v2.3.1"
APP_CODENAME = "Beaufort 🧀"
APP_SUBTITLE = "Naviguez le Grand Paris, tout simplement."

# ==========================================
#              CONFIGURATION API
# ==========================================
try:
    API_KEY = st.secrets["IDFM_API_KEY"]
except (FileNotFoundError, KeyError):
    API_KEY = "TA_CLE_ICI_SI_BESOIN_EN_LOCAL"

BASE_URL = "https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia"

# ==========================================
#              CONSTANTES MÉTIER
# ==========================================
HIERARCHIE = {"RER": 1, "TRAIN": 2, "METRO": 3, "CABLE": 4, "TRAM": 5, "BUS": 6, "AUTRE": 99}

GEOGRAPHIE_RER = {
    "A": {
        "labels": ("⇦ OUEST (Cergy / Poissy / St-Germain)", "⇨ EST (Marne-la-Vallée / Boissy)"),
        "mots_1": ["CERGY", "POISSY", "GERMAIN", "RUEIL", "DEFENSE", "DÉFENSE", "NANTERRE", "VESINET", "MAISONS", "LAFFITTE", "PECQ", "ACHERES", "GRANDE ARCHE", "SARTROUVILLE"],
        "term_1": ["HAUT", "POISSY", "GERMAIN"],
        "mots_2": ["MARNE", "BOISSY", "TORCY", "NATION", "VINCENNES", "FONTENAY", "NOISY", "JOINVILLE", "VALLEE", "CHESSY", "DISNEY"],
        "term_2": ["CHESSY", "BOISSY"]
    },
    "B": {
        "labels": ("⇩ SUD (St-Rémy / Robinson)", "⇧ NORD (Roissy / Mitry)"),
        "mots_1": ["REMY", "RÉMY", "ROBINSON", "LAPLACE", "DENFERT", "CITE", "MASSY", "ORSAY", "BOURG", "CROIX", "GENTILLY", "ARCUEIL", "BAGNEUX"],
        "term_1": ["REMY", "RÉMY", "ROBINSON"],
        "mots_2": ["GAULLE", "MITRY", "NORD", "AULNAY", "BOURGET", "LA PLAINE", "CLAYE", "AÉROPORT"],
        "term_2": ["GAULLE", "MITRY"]
    },
    "C": {
        "labels": ("⇦ OUEST (Versailles / Pontoise)", "⇨ SUD/EST (Massy / Dourdan / Étampes)"),
        "mots_1": ["INVALIDES", "AUSTERLITZ", "VERSAILLES", "QUENTIN", "PONTOISE", "CHAMP", "EIFFEL", "CHAVILLE", "ERMONT", "JAVEL", "ALMA", "VELIZY", "BEAUCHAMP", "MONTIGNY", "ARGENTEUIL"],
        "term_1": ["VERSAILLES", "QUENTIN", "PONTOISE", "AUSTERLITZ"],
        "mots_2": ["MASSY", "DOURDAN", "ETAMPES", "ÉTAMPES", "MARTIN", "JUVISY", "BIBLIOTHEQUE", "ORLY", "RUNGIS", "BRETIGNY", "BRÉTIGNY", "CHOISY", "IVRY", "ATHIS", "SAVIGNY"],
        "term_2": ["DOURDAN", "ETAMPES", "ÉTAMPES", "MASSY", "BRÉTIGNY"]
    },
    "D": {
        "labels": ("⇩ SUD (Melun / Corbeil)", "⇧ NORD (Creil)"),
        "mots_1": ["MELUN", "CORBEIL", "MALESHERBES", "VILLENEUVE", "COMBS", "FERTE", "LIEUSAINT", "MOISSELLES", "JUVISY"],
        "term_1": ["MELUN", "CORBEIL", "MALESHERBES"],
        "mots_2": ["CREIL", "GOUSSAINVILLE", "ORRY", "VILLIERS", "STADE", "DENIS", "LOUVRES", "SURVILLIERS", "GARE DE LYON", "PARIS", "CHATELET", "NORD"],
        "term_2": ["CREIL", "ORRY", "GOUSSAINVILLE"]
    },
    "E": {
        "labels": ("⇦ OUEST (Nanterre)", "⇨ EST (Chelles / Tournan)"),
        "mots_1": ["HAUSSMANN", "LAZARE", "MAGENTA", "NANTERRE", "DEFENSE", "DÉFENSE", "ROSA"],
        "term_1": ["NANTERRE", "HAUSSMANN"],
        "mots_2": ["CHELLES", "TOURNAN", "VILLIERS", "GAGNY", "EMERAINVILLE", "ROISSY", "NOISY", "BONDY"],
        "term_2": ["CHELLES", "TOURNAN"]
    },
    "H": {
        "labels": ("⇧ NORD (Pontoise / Persan / Creil)", "⇩ PARIS NORD"),
        "mots_1": ["PONTOISE", "PERSAN", "BEAUMONT", "LUZARCHES", "CREIL", "MONTSOULT", "VALMONDOIS", "SARROUS", "SAINT-LEU", "SARCELLES", "BRICE"],
        "term_1": ["PONTOISE", "PERSAN", "LUZARCHES", "CREIL"],
        "mots_2": ["PARIS", "NORD"],
        "term_2": ["PARIS", "NORD"]
    },
    "J": {
        "labels": ("⇦ OUEST (Mantes / Gisors / Ermont)", "⇨ PARIS ST-LAZARE"),
        "mots_1": ["MANTES", "JOLIE", "GISORS", "ERMONT", "VERNON", "PONTOISE", "CONFLANS", "BOISSY", "MEULAN", "MUREAUX", "CORMEILLES", "ARGENTEUIL", "ISSOU"],
        "term_1": ["MANTES", "GISORS", "ERMONT", "VERNON"],
        "mots_2": ["PARIS", "LAZARE"],
        "term_2": ["PARIS", "LAZARE"]
    },
    "K": {
        "labels": ("⇧ NORD (Crépy-en-Valois)", "⇩ PARIS NORD"),
        "mots_1": ["CREPY", "CRÉPY", "DAMMARTIN"],
        "term_1": ["CREPY", "CRÉPY"],
        "mots_2": ["PARIS", "NORD"],
        "term_2": ["PARIS", "NORD"]
    },
    "L": {
        "labels": ("⇦ OUEST (Versailles / St-Nom / Cergy)", "⇨ PARIS ST-LAZARE"),
        "mots_1": ["VERSAILLES", "NOM", "BRETÈCHE", "CERGY", "NANTERRE", "MAISONS", "CLOUD", "SARTROUVILLE"],
        "term_1": ["VERSAILLES", "NOM", "HAUT"],       
        "mots_2": ["PARIS", "LAZARE"],
        "term_2": ["PARIS", "LAZARE"]
    },
    "N": {
        "labels": ("⇦ OUEST (Rambouillet / Dreux / Mantes)", "⇨ PARIS MONTPARNASSE"),
        "mots_1": ["RAMBOUILLET", "DREUX", "MANTES", "JOLIE", "PLAISIR", "SEVRES", "SÈVRES"],
        "term_1": ["RAMBOUILLET", "DREUX", "MANTES"],
        "mots_2": ["PARIS", "MONTPARNASSE"],
        "term_2": ["PARIS", "MONTPARNASSE"]
    },
    "P": {
        "labels": ("⇨ EST (Meaux / Provins / Coulommiers)", "⇦ PARIS EST"),
        "mots_1": ["MEAUX", "CHATEAU", "CHÂTEAU", "THIERRY", "FERTE", "FERTÉ", "MILON", "PROVINS", "COULOMMIERS"],
        "term_1": ["MEAUX", "CHÂTEAU", "PROVINS", "COULOMMIERS", "FERTÉ"],
        "mots_2": ["PARIS", "EST"],
        "term_2": ["PARIS", "EST"]
    },
    "R": {
        "labels": ("⇩ SUD (Montereau / Montargis)", "⇧ PARIS GARE DE LYON"),
        "mots_1": ["MONTEREAU", "MONTARGIS", "MELUN"],
        "term_1": ["MONTEREAU", "MONTARGIS"],
        "mots_2": ["PARIS", "LYON", "BERCY"],
        "term_2": ["PARIS", "LYON"]
    },
    "U": {
        "labels": ("⇩ SUD (La Verrière)", "⇧ NORD (La Défense)"),
        "mots_1": ["VERRIERE", "VERRIÈRE", "TRAPPES"],
        "term_1": ["VERRIERE", "VERRIÈRE"],
        "mots_2": ["DEFENSE", "DÉFENSE"],
        "term_2": ["DEFENSE", "DÉFENSE"]
    },
    "V": {
        "labels": ("⇦ OUEST (Versailles-Chantiers)", "⇨ EST (Massy-Palaiseau)"),
        "mots_1": ["VERSAILLES", "CHANTIERS"],
        "term_1": ["VERSAILLES"],
        "mots_2": ["MASSY", "PALAISEAU"],
        "term_2": ["MASSY"]
    }
}

TOPOLOGIE_LIGNES = {
    "A": {
        "nom_aller": "⇨ EST (Marne-la-Vallée / Boissy)",
        "nom_retour": "⇦ OUEST (Cergy / Poissy / St-Germain)",
        "routes": [
            # 1. Axe classique : St-Germain <-> Boissy
            ["GERMAIN", "PECQ", "VESINET", "CHATOU", "RUEIL", "NANTERRE", "DEFENSE", "GAULLE", "AUBER", "CHATELET", "LYON", "NATION", "VINCENNES", "FONTENAY-SOUS", "NOGENT", "JOINVILLE", "MAUR", "CHAMPIGNY", "VARENNE", "SUCY", "BOISSY"],
            
            # 2. Axe classique : Cergy <-> Marne-la-Vallée
            ["CERGY", "NEUVILLE", "CONFLANS", "ACHERES", "MAISONS", "SARTROUVILLE", "HOUILLES", "NANTERRE", "DEFENSE", "GAULLE", "AUBER", "CHATELET", "LYON", "NATION", "VINCENNES", "VAL DE FONTENAY", "NEUILLY", "BRY", "NOISY", "LOGNES", "TORCY", "BUSSY", "EUROPE", "CHESSY"],
            
            # 3. Axe classique : Poissy <-> Marne-la-Vallée
            ["POISSY", "ACHERES", "MAISONS", "SARTROUVILLE", "HOUILLES", "NANTERRE", "DEFENSE", "GAULLE", "AUBER", "CHATELET", "LYON", "NATION", "VINCENNES", "VAL DE FONTENAY", "NEUILLY", "BRY", "NOISY", "LOGNES", "TORCY", "BUSSY", "EUROPE", "CHESSY"],
            
            # 4. Axe "Nuit/Travaux" : Cergy <-> Boissy (Au cas où !)
            ["CERGY", "NEUVILLE", "CONFLANS", "ACHERES", "MAISONS", "SARTROUVILLE", "HOUILLES", "NANTERRE", "DEFENSE", "GAULLE", "AUBER", "CHATELET", "LYON", "NATION", "VINCENNES", "FONTENAY-SOUS", "NOGENT", "JOINVILLE", "MAUR", "CHAMPIGNY", "VARENNE", "SUCY", "BOISSY"],
            
            # 5. Axe "Nuit/Travaux" : St-Germain <-> Marne-la-Vallée (Au cas où !)
            ["GERMAIN", "PECQ", "VESINET", "CHATOU", "RUEIL", "NANTERRE", "DEFENSE", "GAULLE", "AUBER", "CHATELET", "LYON", "NATION", "VINCENNES", "VAL DE FONTENAY", "NEUILLY", "BRY", "NOISY", "LOGNES", "TORCY", "BUSSY", "EUROPE", "CHESSY"]
        ]
    }, # <--- LA CORRECTION EST ICI : on ferme le dictionnaire de la ligne A avec "},"

    "B": {
        "nom_aller": "⇧ NORD (Aéroport CDG / Mitry)",
        "nom_retour": "⇩ SUD (St-Rémy / Robinson)",
        "routes": [
            # 1. Axe : St-Rémy <-> Mitry
            ["REMY", "COURCELLE", "GIF", "BURES", "ORSAY", "LOZERE", "PALAISEAU", "MASSY", "VERRIERES", "FONTAINE", "CROIX", "BOURG", "BAGNEUX", "ARCUEIL", "LAPLACE", "GENTILLY", "CITE UNIVERSITAIRE", "DENFERT", "ROYAL", "LUXEMBOURG", "MICHEL", "CHATELET", "EST", "NORD", "PLAINE", "COURNEUVE", "BOURGET", "DRANCY", "BLANC", "AULNAY", "SEVRAN LIVRY", "VERT GALANT", "VILLEPARISIS", "MITRY"],
            
            # 2. Axe : Robinson <-> Aéroport CDG
            ["ROBINSON", "FONTENAY", "SCEAUX", "BOURG", "BAGNEUX", "ARCUEIL", "LAPLACE", "GENTILLY", "CITE UNIVERSITAIRE", "DENFERT", "ROYAL", "LUXEMBOURG", "MICHEL", "CHATELET", "EST", "NORD", "PLAINE", "COURNEUVE", "BOURGET", "DRANCY", "BLANC", "AULNAY", "SEVRAN BEAUDOTTES", "VILLEPINTE", "PARC", "GAULLE"]
        ]
    },

    "C": {
        "nom_aller": "⇨ SUD/EST (Massy / Dourdan / Étampes)",
        "nom_retour": "⇦ OUEST (Versailles / Pontoise / St-Quentin)",
        "routes": [
            # 1. Axe Pontoise <-> Massy Palaiseau (via Pont de Rungis)
            ["PONTOISE", "AUMONE", "LIESSE", "PIERRELAYE", "MONTIGNY", "FRANCONVILLE", "CERNAY", "ERMONT", "GRATIEN", "EPINAY SUR SEINE", "GENNEVILLIERS", "GRESILLONS", "SAINT-OUEN", "CLICHY", "PEREIRE", "MAILLOT", "FOCH", "HENRI MARTIN", "BOULAINVILLIERS", "KENNEDY", "CHAMP DE MARS", "ALMA", "INVALIDES", "ORSAY", "MICHEL", "AUSTERLITZ", "BIBLIOTHEQUE", "IVRY", "VITRY", "ARDOINES", "CHOISY", "SAULES", "ORLY", "RUNGIS", "FRATERNELLE", "CHEMIN D'ANTONY", "VERRIERES", "MASSY PALAISEAU"],
            
            # 2. Axe St-Quentin <-> Étampes
            ["QUENTIN", "CYR", "VERSAILLES CHANTIERS", "PORCHEFONTAINE", "VIROFLAY", "CHAVILLE", "MEUDON", "ISSY", "VAL DE SEINE", "GARIGLIANO", "JAVEL", "CHAMP DE MARS", "ALMA", "INVALIDES", "ORSAY", "MICHEL", "AUSTERLITZ", "BIBLIOTHEQUE", "IVRY", "VITRY", "ARDOINES", "CHOISY", "VILLENEUVE LE ROI", "ABLON", "ATHIS", "JUVISY", "SAVIGNY", "EPINAY SUR ORGE", "GENEVIEVE", "MICHEL SUR ORGE", "BRETIGNY", "MAROLLES", "BOURAY", "LARDY", "CHAMARANDE", "ETRECHY", "ETAMPES"],

            # 3. Axe Versailles Château <-> Dourdan
            ["VERSAILLES CHATEAU", "PORCHEFONTAINE", "VIROFLAY", "CHAVILLE", "MEUDON", "ISSY", "VAL DE SEINE", "GARIGLIANO", "JAVEL", "CHAMP DE MARS", "ALMA", "INVALIDES", "ORSAY", "MICHEL", "AUSTERLITZ", "BIBLIOTHEQUE", "IVRY", "VITRY", "ARDOINES", "CHOISY", "VILLENEUVE LE ROI", "ABLON", "ATHIS", "JUVISY", "SAVIGNY", "EPINAY SUR ORGE", "GENEVIEVE", "MICHEL SUR ORGE", "BRETIGNY", "NORVILLE", "ARPAJON", "EGLY", "BREUILLET", "CHERON", "SERMAISE", "DOURDAN"],
            
            # 4. La boucle Sud (Massy -> Versailles Chantiers via la vallée de la Bièvre)
            ["JUVISY", "SAVIGNY", "EPINAY SUR ORGE", "GRAVIGNY", "PETIT VAUX", "MASSY PALAISEAU", "IGNY", "BIEVRES", "VAUBOYEN", "JOUY", "PETIT JOUY", "VERSAILLES CHANTIERS"]
        ]
    },

    "D": {
        "nom_aller": "⇩ SUD (Melun / Corbeil / Malesherbes)",
        "nom_retour": "⇧ NORD (Creil / Orry)",
        "routes": [
            # 1. Axe Nord <-> Sud (via Combs-la-Ville)
            ["CREIL", "CHANTILLY", "BORNE BLANCHE", "SURVILLIERS", "LOUVRES", "NOUES", "GOUSSAINVILLE", "VILLIERS LE BEL", "GONESSE", "GARGES", "PIERREFITTE", "DENIS", "STADE DE FRANCE", "NORD", "CHATELET", "LYON", "MAISONS ALFORT", "ALFORTVILLE", "VERT DE MAISONS", "POMPADOUR", "TRIAGE", "VILLENEUVE SAINT-GEORGES", "MONTGERON", "YERRES", "BRUNOY", "BOUSSY", "COMBS", "LIEUSAINT", "SAVIGNY LE TEMPLE", "CESSON", "MEE", "MELUN"],
            
            # 2. Axe Centre <-> Malesherbes (via le Plateau - Evry Courcouronnes)
            ["CREIL", "CHANTILLY", "BORNE BLANCHE", "SURVILLIERS", "LOUVRES", "NOUES", "GOUSSAINVILLE", "VILLIERS LE BEL", "GONESSE", "GARGES", "PIERREFITTE", "DENIS", "STADE DE FRANCE", "NORD", "CHATELET", "LYON", "MAISONS ALFORT", "ALFORTVILLE", "VERT DE MAISONS", "POMPADOUR", "TRIAGE", "VILLENEUVE SAINT-GEORGES", "VIGNEUX", "JUVISY", "VIRY", "GRIGNY", "ORANGIS BOIS", "COURCOURONNES", "BRAS DE FER", "CORBEIL", "MOULIN GALANT", "MENNECY", "BALLANCOURT", "FERTE ALAIS", "BOUTIGNY", "MAISSE", "BUNO", "GIRONVILLE", "MALESHERBES"],
            
            # 3. Axe Centre <-> Melun (via la Vallée - Evry Val de Seine)
            ["CREIL", "CHANTILLY", "BORNE BLANCHE", "SURVILLIERS", "LOUVRES", "NOUES", "GOUSSAINVILLE", "VILLIERS LE BEL", "GONESSE", "GARGES", "PIERREFITTE", "DENIS", "STADE DE FRANCE", "NORD", "CHATELET", "LYON", "MAISONS ALFORT", "ALFORTVILLE", "VERT DE MAISONS", "POMPADOUR", "TRIAGE", "VILLENEUVE SAINT-GEORGES", "VIGNEUX", "JUVISY", "VIRY", "RIS ORANGIS", "GRAND BOURG", "VAL DE SEINE", "CORBEIL", "ESSONNES ROBINSON", "VILLABE", "PLESSIS CHENET", "COUDRAY", "PONTHIERRY", "VOSVES", "MELUN"]
        ]
    },

    "E": {
        "nom_aller": "⇨ EST (Chelles / Tournan)",
        "nom_retour": "⇦ OUEST (Nanterre / Saint-Lazare)",
        "routes": [
            # 1. Branche Chelles-Gournay
            ["NANTERRE", "DEFENSE", "MAILLOT", "HAUSSMANN", "MAGENTA", "ROSA PARKS", "PANTIN", "NOISY", "BONDY", "RAINCY", "CHENAY", "CHELLES"],
            
            # 2. Branche Tournan
            ["NANTERRE", "DEFENSE", "MAILLOT", "HAUSSMANN", "MAGENTA", "ROSA PARKS", "PANTIN", "NOISY", "ROSNY BOIS PERRIER", "ROSNY SOUS BOIS", "VAL DE FONTENAY", "NOGENT", "BOULLEREAUX", "VILLIERS", "YVRIS", "EMERAINVILLE", "ROISSY", "OZOIR", "GRETZ", "TOURNAN"]
        ]
    }
}
