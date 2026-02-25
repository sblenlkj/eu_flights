from dotenv import load_dotenv
import os

from graph_creation.application.use_case import CreateAndSaveGraphUseCase
from graph_creation.application.services import CreateGraphService, ExportGraphService
from graph_creation.adapters.input import CsvMunicipalityRepository, OpenSkyFlightProvider
from graph_creation.adapters.output import FoliumMapExporter, GraphJsonExporter


load_dotenv("./graph_creation/.env")

def bootsrap_create_save_graph_use_case() -> CreateAndSaveGraphUseCase:
    """Bootstrap the CreateAndSaveGraphUseCase with all its dependencies."""

    municipality_repo = CsvMunicipalityRepository("./data/municipality.csv")

    flight_provider = OpenSkyFlightProvider(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET")
    )
    create_graph_service = CreateGraphService(
        municipality_repo=municipality_repo,
        flight_provider=flight_provider
    )

    json_exporter = GraphJsonExporter()
    folium_exporter = FoliumMapExporter()
    export_graph_service = ExportGraphService(output_adapters_lst=[json_exporter, folium_exporter])

    return CreateAndSaveGraphUseCase(
        create_graph_service=create_graph_service,
        export_graph_service=export_graph_service
    )