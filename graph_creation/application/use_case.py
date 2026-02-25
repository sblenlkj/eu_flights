from graph_creation.application.services import CreateGraphService, ExportGraphService

class CreateAndSaveGraphUseCase:
    def __init__(
        self,
        create_graph_service: CreateGraphService,
        export_graph_service: ExportGraphService
    ):
        self.create_graph_service = create_graph_service
        self.export_graph_service = export_graph_service

    def run(self, day_start: str, day_interval_number:int=1, graph_name:str="some_graph") -> None:
        """Create a graph for the given day and export it using the provided export services.  
        
        day_start should be sent in "%Y-%m-%d" format.  
        day_interval_number is the number of days to include in the graph, starting from day_start. Default is 1 (only the day_start).
        graph_name will be used as the file name for the exported graph (without extension). 
        It will be saved in the "data" directory with an appropriate extension based on the export service used.
        """
        graph = self.create_graph_service.execute_since_the_day(day_start, day_interval_number)
        self.export_graph_service.export(graph, file_name=graph_name)