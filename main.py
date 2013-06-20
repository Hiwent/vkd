#!/usr/bin/env python2

"""Save everything from your VK wall"""

__author__ = "Rast"

import logging
import argparse
from collections import defaultdict
from PostParser import PostParser
from Api import call_api, auth
import os

def arg_parse():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-d", "--dir",
                        type=str,
                        help="Directory to store dumped data",
                        dest="directory",
                        required=False,
                        default=".")
    argparser.add_argument("-i", "--id",
                        type=int,
                        help="User ID to dump. To dump a group, specify its ID with '-' prefix",
                        metavar="USER_ID|-GROUP_ID",
                        dest="id",
                        required=True)
    argparser.add_argument("-t", "--token",
                        type=str,
                        help="Access token, generated by VK for session",
                        dest="token",
                        required=False)
    argparser.add_argument("-a", "--app_id",
                        type=int,
                        help="Your application ID to access VK API",
                        dest="app_id",
                        required=True)
    argparser.add_argument("-m", "--mode",
                        option_strings=['wall', 'audio', 'video', 'notes'],
                        nargs="+",
                        help="What to dump. Possible values: "+', '.join(['wall', 'audio', 'video', 'notes']),
                        dest="mode",
                        required=True)

    argparser.add_argument("--wall_start",
                        type=int,
                        help="Post number to start from (first is 0)",
                        dest="wall_start",
                        required=False,
                        metavar="INT",
                        default=0)
    argparser.add_argument("--wall_end",
                        type=int,
                        help="Post number to end at (0 = all posts)",
                        dest="wall_end",
                        required=False,
                        metavar="INT",
                        default=0)

    argparser.add_argument("--audio_start",
                        type=int,
                        help="Audio number to start from (first is 0)",
                        dest="audio_start",
                        required=False,
                        metavar="INT",
                        default=0)
    argparser.add_argument("--audio_end",
                        type=int,
                        help="Audio number to end at (0 = all audios)",
                        dest="audio_end",
                        required=False,
                        metavar="INT",
                        default=0)

    argparser.add_argument("--video_start",
                        type=int,
                        help="Video number to start from (first is 0)",
                        dest="video_start",
                        required=False,
                        metavar="INT",
                        default=0)
    argparser.add_argument("--video_end",
                        type=int,
                        help="Video number to end at (0 = all videos)",
                        dest="video_end",
                        required=False,
                        metavar="INT",
                        default=0)

    argparser.add_argument("--notes_start",
                        type=int,
                        help="Note number to start from (first is 0)",
                        dest="notes_start",
                        required=False,
                        metavar="INT",
                        default=0)
    argparser.add_argument("--notes_end",
                        type=int,
                        help="Note number to end at (0 = all notes)",
                        dest="notes_end",
                        required=False,
                        metavar="INT",
                        default=0)

    argparser.add_argument("-v", "--verbose", action="store_true",
                        help="Print more info to STDOUT while processing")
    argparser.add_argument("--no-download",
                        action="store_true",
                        help="Do not download attachments, only store links",
                        dest="no_download",
                        required=False)
    args = argparser.parse_args()
    return args

def process_post(number, post_data, post_parser, json_stuff):
    """Post-processing :)"""
    data = defaultdict(lambda: "", post_data[1])
    post_parser(number, data, json_stuff)

def process_audio(number, audio_data, post_parser, json_stuff):
    """Audio-processing"""
    #data = defaultdict(lambda: "", audio_data[1])
    data = {'attachments': [{'type': 'audio',
                            'audio': audio_data[0],
                            }],
            'id' : ''
            }

    post_parser(number, data, json_stuff)


def ranges(start, end, count):
    """Determine ranges"""
    if end == 0:
        end = count
    if not 0 <= start < count + 1:
        raise RuntimeError("Start argument not in valid range")
    if not start <= end <= count:
        raise RuntimeError("End argument not in valid range")
    logging.info("Parsing posts from {} to {}".format(start, end))
    total = end - start
    return start, end, total

def main():
    """Main function"""
    access_rights = ["wall", "audio", "friends", "notes", "video"]

    args = arg_parse()
    args.token = auth(args, access_rights) if args.token is None else args.token
    if args.token is None:
        raise RuntimeError("Access token not found")


    if 'wall' in args.mode:
        #determine posts count
        (response, json_stuff) = call_api("wall.get", [("owner_id", args.id), ("count", 1), ("offset", 0)], args.token)
        count = response[0]
        logging.info("Total posts: {}".format(count))

        args.wall_start, args.wall_end, total = ranges(args.wall_start, args.wall_end, count)
        counter = 0.0  # float for %
        post_parser = PostParser(args.directory, str(args.id), args)
        for x in xrange(args.wall_start, args.wall_end):
            if args.verbose and x % 50 == 0:
                print("Done: {:.2%} ({})".format(counter / total, int(counter)))
            (post, json_stuff) = call_api("wall.get", [("owner_id", args.id), ("count", 1), ("offset", x)], args.token)
            process_post(("wall post", x), post, post_parser, json_stuff)
            counter += 1
        if args.verbose:
            print("Done: {:.2%} ({})".format(float(total) / total, int(total)))

    if 'audio' in args.mode:
        #determine audio count
        (response, json_stuff) = call_api("audio.getCount", [("oid", args.id)], args.token)
        count = response
        logging.info("Total audio tracks: {}".format(count))

        args.audio_start, args.audio_end, total = ranges(args.audio_start, args.audio_end, count)
        counter = 0.0  # float for %
        audio_dir = os.path.join(str(args.id), 'audio')
        post_parser = PostParser(args.directory, audio_dir, args)
        id_param = "uid" if args.id > 0 else "gid"
        args.id *= -1 if args.id < 0 else 1
        for x in xrange(args.audio_start, args.audio_end):
            if args.verbose and x % 50 == 0:
                print("Done: {:.2%} ({})".format(counter / total, int(counter)))
            (audio, json_stuff) = call_api("audio.get", [(id_param, args.id), ("count", 1), ("offset", x)], args.token)
            process_audio(("audiotrack", x), audio, post_parser, json_stuff)
            counter += 1
        if args.verbose:
            print("Done: {:.2%} ({})".format(float(total) / total, int(total)))

    if 'video' in args.mode:
        raise NotImplementedError("Video mode is not written yet, sorry :(")
    if 'notes' in args.mode:
        raise NotImplementedError("Notes mode is not written yet, sorry :(")

if __name__ == '__main__':
    logging.basicConfig(format=u"""%(filename).6s : %(lineno)4d #%(levelname).8s [%(asctime)s] %(message)s""",
                            level=logging.DEBUG,
                            filename=u'report.log')
    ok = False
    try:
        logging.info("Start")
        main()
        logging.info("End")
        ok = True
    except KeyboardInterrupt:
        logging.critical("Interrupted by keystroke")
        print "\nWhy, cruel world?.."
    finally:
        if not ok:
            logging.critical("Fail")
