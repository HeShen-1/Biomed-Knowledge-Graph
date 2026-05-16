from tasks.celery_app import celery_app
from ingest.sources.pubmed import PubMedIngester
from ingest.sources.uniprot import UniProtIngester
from ingest.sources.chembl import ChEMBLIngester
from ingest.sources.opentargets import OpenTargetsIngester
from ingest.sources.string import StringIngester
from ingest.pipeline import Pipeline


@celery_app.task(name="sync_source")
def sync_source(source: str):
    import asyncio
    ingesters = {
        "pubmed": PubMedIngester,
        "uniprot": UniProtIngester,
        "chembl": ChEMBLIngester,
        "opentargets": OpenTargetsIngester,
        "string": StringIngester,
    }
    ingester_cls = ingesters.get(source)
    if not ingester_cls:
        return {"error": f"unknown source: {source}"}
    ingester = ingester_cls()
    pipeline = Pipeline(ingester)
    return asyncio.run(pipeline.run())
