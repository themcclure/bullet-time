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
import datetime
import shutil
import frontmatter

import ballistics.utils
from ballistics import config, BeanCollection, merge_markdown, RoastCollection, generate_large_label
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


def ingest_roasts(coll: RoastCollection):
    """
    Take in a collection of Roasts, and "ingest" them - ie, turn them into markdown in the output directory.
    :param coll: RoastCollection to process
    """
    # TODO: if the collections could iterate, this function could service both ingesting beans and roasts
    for roast in coll.roasts:
        log.debug(f"Ingesting {roast.name}")
        roast.to_markdown()
        roast.generate_labels()
        # TODO: generate profile graph


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


def publish_blends() -> int:
    """
    Take all the manually created blends markdown.
    Save the markdown object to the publish directory for delivery to the website.
    :return: the number of files put in the published folder
    """
    published_files = 0
    origin_dir = config.annotationsDir / "blends"
    publish_dir = config.publishDir / "blends"
    publish_img_dir = publish_dir / "images"
    if not publish_img_dir.exists():
        publish_img_dir.mkdir(parents=True)
    for blendf in origin_dir.glob('*.md'):
        blend_name = blendf.stem
        log.debug(f"Processing blend: {blendf}")
        meta = frontmatter.load(blendf).metadata
        slug = meta['slug']
        batch = f"{(meta['batch']):03d}"  # format the number as 3 digits with leading 0s
        name = meta['title']
        labelf = publish_img_dir / f"{slug}.png"
        url = f"{config.baseUrl}blends/{slug}"
        img = generate_large_label(config.labels['large'], batch, name, url, False, datetime.datetime.today(),
                                   datetime.datetime.today(), datetime.datetime.today()+datetime.timedelta(days=14))
        shutil.copy2(blendf, publish_dir)
        img.save(labelf)
        published_files += 1
    return published_files


def publish_roasts() -> int:
    """
    Take all the raw roasts markdown, for each bean look for an override markdown file for it.
    If found, merge into combined markdown object.
    Save the markdown object to the publish directory for delivery to the website.
    :return: the number of files put in the published folder
    """
    published_files = 0
    origin_dir = config.outputDir / "roasts"
    annotation_dir = config.annotationsDir / "roasts"
    publish_dir = config.publishDir / "roasts"
    image_dir = config.publishDir / "roasts/images"
    if not image_dir.exists():
        image_dir.mkdir(parents=True)
    for roastf in origin_dir.glob('*.md'):
        roast_name = roastf.name
        annotf = annotation_dir / roast_name
        log.debug(f"Attempting to merge {roastf} and {annotf}")
        roast_merged = merge_markdown(roastf, annotf)
        # write out meta + content as single md file
        with open(publish_dir / roast_name, "wt") as pubf:
            pubf.write(roast_merged)
            published_files += 1
        labelf = origin_dir / f"images/{roastf.stem}.png"
        log.debug(f"Looking for this doc {labelf}")
        if labelf.exists():
            log.debug(f"copying {labelf} to {image_dir}")
            shutil.copy2(labelf, image_dir)
    return published_files


if __name__ == '__main__':
    bc = BeanCollection()
    rc = RoastCollection()
    log = config.logger
    ingest_beans(bc)
    log.info(f"Ingested {len(bc.beans)} beans into {config.outputDir}")
    num_pub = publish_beans()
    log.info(f"Published {num_pub} of {len(bc.beans)} beans into {config.publishDir}")
    ingest_roasts(rc)
    log.info(f"Ingested {len(rc.roasts)} roasts into {config.outputDir}")
    num_pub = publish_roasts()
    log.info(f"Published {num_pub} of {len(bc.beans)} roasts into {config.publishDir}")
    # blends are a little bit different, as there is no RT/RW data to bring in
    # so just publish it... but the publishing also needs to create the label
    num_pub = publish_blends()
    log.info(f"Published {num_pub} blends into {config.publishDir}")
