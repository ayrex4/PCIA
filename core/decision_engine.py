from utils.logger import get_logger

logger = get_logger("DecisionEngine")

class DecisionEngine:
    def __init__(self):
        # We define a hierarchy of reliability
        pass

    def select_strategy(self, task):
        """
        task format: 
        {
            "intent": "click", 
            "target_type": "text" | "icon" | "system" | "unknown",
            "target_value": "Login" | "path/to/icon.png" | {"app": "Chrome", "element": "Reload"}
        }
        """
        logger.info(f"Evaluating strategy for task: {task['intent']} -> {task['target_value']}")
        
        target_type = task.get("target_type")
        
        # Primary Strategy Selection Matrix
        if target_type == "vision":
            logger.info("Decision: Vision AI (General Object Detection)")
            return ["vision"] # The most expensive but most powerful strategy
                    
        elif target_type == "text":
            logger.info("Decision: OCR (High Reliability for text)")
            return ["ocr", "vision_ai"]
            
        elif target_type == "icon":
            logger.info("Decision: Template Matching (High Reliability for statics)")
            return ["template_matching", "vision_ai"]
            
        else:
            logger.info("Decision: Vision AI (Complex/Unknown Interface)")
            return ["vision_ai"]