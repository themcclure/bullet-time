"""
This script processes all the roasts and beans in the RoasTime directory.

The first stage of processing means turning the data into a semi-structured markdown (.md) file and putting them in the
output directory.

The intent is that, using a Markdown editor of some kind, a person can add supplemental information that isn't in the
RoasTime ecosystem (tasting notes, scores, other data).

A second stage of processing involves taking the raw and supplemental Markdown files, compiling them into a single file
for each roast and bean, and saving those files in a publish directory.
The intent here is that some website generator takes that information to publish it to a website.
I use gatsbyjs for this, and have a related project that takes this in and publishes it.
"""
from typing import Union

# import ballistics
import frontmatter
from ballistics import config, BeanCollection, merge_markdown, RoastCollection
from pprint import pprint


##########
# Config
##########


def ingest_beans(coll: BeanCollection):
    """
    Take in a collection of Beans, and "ingest" them - ie, turn them into markdown in the output directory.
    :param coll: BeanCollection to process
    """
    # TODO: if the collections could iterate, this function could service both ingesting beans and roasts
    for bean in coll.beans:
        log.debug(f"Ingesting {bean.name}")
        bean.to_markdown()


def publish_beans() -> int:
    """
    Take all the raw beans markdown, for each bean look for an override markdown file for it.
    If found, merge into combined markdown object.
    Save the markdown object to the publish directory for delivery to the website.
    :return: the number of files put in the published folder
    """
    published_files = 0
    origin_dir = config.outputDir / "beans"
    annotation_dir = config.annotationsDir / "beans"
    publish_dir = config.publishDir / "beans"
    if not publish_dir.exists():
        publish_dir.mkdir(parents=True)
    for beanf in origin_dir.glob('*.md'):
        bean_name = beanf.name
        annotf = annotation_dir / bean_name
        log.debug(f"Attempting to merge {beanf} and {annotf}")
        bean_merged = merge_markdown(beanf, annotf)
        # write out meta + content as single md file
        with open(publish_dir / bean_name, "wt") as pubf:
            pubf.write(bean_merged)
            published_files += 1
    return published_files


if __name__ == '__main__':
    bc = BeanCollection()
    rc = RoastCollection()
    # TODO: roasts collection
    log = config.logger
    ingest_beans(bc)
    # TODO: roasts
    # ingest_roasts(rc)
    log.info(f"Ingested {len(bc.beans)} beans into {config.outputDir}")
    num_pub = publish_beans()
    log.info(f"Published {num_pub} of {len(bc.beans)} beans into {config.publishDir}")
    # TODO: publisj the annotated roasts
