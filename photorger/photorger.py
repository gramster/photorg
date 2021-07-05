import glob
import hashlib
import os
import pickle
import re
import sys
from datetime import datetime
from pathlib import Path
from shutil import copyfile

import exifread


# Command-line settings
source = os.getcwd()
target = os.getcwd()
noclean = True
nodeep = False
nocache = True
norename = False
pretend = False
copy = False
verbose = False
newest = False
oldest = False
shortest = False
longest = False
force = False

# use_rename means use os.rename rather than file copy. We default to this and turn
# it off if rename fails, which may be because the source and destination are on 
# different file systems so copy is the only option.
use_rename = True

# RegExps used to get date info from file paths
# These would need some fixing for Windows
path_re1=re.compile('^(.*)/([12][90][01289][0-9])/([01][0-9])/([0123][0-9])/(.*)$')
path_re2=re.compile('^(.*)/([12][90][01289][0-9])/([01][0-9])/(.*)$')
path_re3=re.compile('^(.*)/([12][90][01289][0-9])/(.*)$')

# Load the cache
cachefile = target + '/.photorger.cache'
done = set()
if os.path.exists(cachefile):
  with open(cachefile, 'rb') as f:
    done = pickle.load(f)


def save_cache():
    if not nocache and not pretend:
        with open(cachefile + '.tmp', 'wb') as f:
          pickle.dump(done, f)
        os.replace(cachefile + '.tmp', cachefile)


def get_exif_tags(fname):
    try:
        with open(fname, 'rb') as f:
            return exifread.process_file(f, details=False)
    except Exception as e:
        return None


def get_exif_date(fname):
    try:
        tags = get_exif_tags(fname)
        if tags is None:
            return None
        parts = str(tags['EXIF DateTimeOriginal']).split(' ')
        msec = 0
        try:
            msec = int(str(tags['EXIF SubSecTimeOriginal']))
        except Exception:
            pass
        created = datetime.fromisoformat(f"{parts[0].replace(':', '-')} {parts[1]}.{msec:03d}")
        return created
    except Exception as e:
        if verbose:
            print(f"Can't get EXIF date from {fname}: {e}")
        return None


BUF_SIZE = 65536

def files_match(src, dst):
    with open(src, "rb") as f1:
        with open(dst, "rb") as f2:
            block1 = block2 = True
            while block1 or block2:
              block1 = f1.read(BUF_SIZE)
              block2 = f2.read(BUF_SIZE)
              if block1 != block2:
                return False
            return True
    return True


def hash_file(fname):
    sha1 = hashlib.sha1()
    with open(fname, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()


def make_folder_for_file(fname):
    if not pretend:
        dpath = fname[:fname.rfind('/')]
        if not os.path.exists(dpath):
            Path(dpath).mkdir(parents=True, exist_ok=True)


def rename_file(src, dst):
    if not pretend:
        os.rename(src, dst)


def remove_file(fname):
    if not pretend:
        os.remove(fname)


def copy_file(src, dst):
    if not pretend:
        copyfile(src, dst)


def relocate_file(src, dst):
    global use_rename
    if use_rename and not copy:
        # we are moving the file with a rename
        try:
            rename_file(src, dst)
            return
        except Exception as e:
            use_rename = False
    
    copy_file(src, dst)
    if not copy:
        remove_file(src)


def move_file(src, dst):
    if os.path.exists(dst):
        if os.path.getsize(src) == os.path.getsize(dst) and (nodeep or files_match(src, dst)):
            if noclean:
                print(f'Rename {src} to {dst} failed: target exists and is duplicate')
            else:
                print(f'Rename {src} to {dst} failed: duplicate target exists; removing source')
                remove_file(src)
            return True
        elif norename:
            print(f'Rename {src} to {dst} failed: target exists and is not duplicate and --norename was used')
            return False
        else: # Target exists and is not a dup; create a new name for target
            split = dst.rfind('.')
            dst0 = dst[:split]
            dst1 = dst[split:]
            i = 1
            while True:
                dst = f'{dst0}({i}){dst1}'
                if not os.path.exists(dst):
                    break
                i += 1

    # Make sure target folder exists
    make_folder_for_file(dst)
    try:
        relocate_file(src, dst)
        print(f'Rename {src} to {dst}')
        return True
    except Exception as e:
        print(f'Rename {src} to {dst} failed: {e}')
        return False


def get_date_from_path(fname):
    # Try to extract a date from the file name or path
    year = 0
    month = 0
    day = 0
    name = fname
    m = path_re1.match(fname)
    if m:
        year = int(m.group(2))
        month = int(m.group(3))
        day = int(m.group(4))
        name = m.group(5)
    else:
        m = path_re2.match(fname)
        if m:
            year = int(m.group(2))
            month = int(m.group(3))
            name = m.group(4)
        else:
            m = path_re3.match(fname)
            if m:
                year = int(m.group(2))
                name = m.group(3)

    # TODO: use file name as a potential date source too
    return year, month, day, name


# Handle names of form "YYYY-MM-DD..." or "...YYYYMMDD..."
iso_date_re = re.compile('(^|[^0-9])([12][90][01289][0-9])-?([01][0-9])-?([0123][0-9])([^0-9]|$)')
# Handle names of form "...Jan 16, 2017..." or "...January 16, 2007..."
txt_date_re1 = re.compile('(^|[^0-9A-Za-z])([A-Za-z]+)[^0-9A-Za-z]+([0-9]{1,2})[^A-Za-z0-9]+([12][90][01289][0-9])($|[^0-9])')
# Handle names of form "...16 Jan, 2017..." or "...16 January, 2007..."
txt_date_re2 = re.compile('(^|[^0-9A-Za-z])([0-9]{1,2})[^0-9A-Za-z]+([A-Za-z]+)[^A-Za-z0-9]+([12][90][01289][0-9])($|[^0-9])')
months = {k: (v+1) for v, k in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}


def get_date_from_name(fname):
    m = iso_date_re.match(fname)
    if m:
        try:
            return datetime(int(m.group(2)), int(m.group(3)), int(m.group(4)))
        except Exception:
            pass

    m = txt_date_re1.match(fname)
    if m:
        month = m.group(2)[:3].lower()
        if month in months.keys():
            try:
                return datetime(int(m.group(4)), months[month], int(m.group(3)))
            except Exception:
                pass

    m = txt_date_re2.match(fname)
    if m:
        month = m.group(3)[:3].lower()
        if month in months.keys():
            try:
                return datetime(int(m.group(4)), months[month], int(m.group(2)))
            except Exception:
                pass

    return None


def move_process(fname):
    # Check location against EXIF data. If there is EXIF data and file is in a date-structured folder
    # but the wrong location, move it.
    # TODO: we have three potential sources of dates: the path, the file name, and the EXIF data.
    # We should fall back to different date tags in EXIF data if we can't get the original date.
    # We should then try to reconcile these three sources, with EXIF data taking priority.
    # We also need to be flexible about date formats.
    created = get_exif_date(fname)
    reason = '(name)'
    from_exif = False
    from_name = False
    if created is None:
        created = get_date_from_name(fname)
    else:
        reason = '(EXIF)'
        from_exif = True
    if created:
        name = fname[fname.rfind('/')+1:]
        dst = f"{target}/{created.year}/{created.month:02d}/{created.day:02d}/{name}"
        year, month, day, name = get_date_from_path(fname)
        if year:
            if year != created.year:
                print(f"{fname} was created at {created} {reason} but is in year folder {year}; move to {dst}")
            elif month != created.month:
                print(f"{fname} was created at {created} {reason} but is in month folder {month}; move to {dst}")
            elif day != created.day:
                print(f"{fname} was created at {created} {reason} but is in day folder {day}; move to {dst}")
            else:
                if verbose:
                    print(f"{fname} was created at {created} {reason} and is properly located")
                done.add(fname)
                return
        else:
            print(f"{fname} was created at {created} {reason} and needs to be moved")

        if move_file(fname, dst):
            done.add(fname)
            done.add(dst)
    else:
        if verbose:
            print(f"Cannot infer creation date for {fname}; skipping")



def info_main(fname):
    # TODO: add more info here
    tags = get_exif_tags(fname)
    if tags:
        for k, v in tags.items():
            print(f'{k:24s}: {v}')


def path_join(a, b):
    # The below doesn't play nice with Synology so do it just with strings
    # return os.path.join(a, b)  
    if a[-1] == '/':
        if b[0] == '/':
            return a + b[1:]
        else:
            return a + b
    else:
        if b[0] == '/':
            return a + b
        else:
            return a + '/' + b


def process_dup_group(group, key=None, descending=False):
    """ Sort group by key then pop off all leading elements with same key. """
    s = sorted(group, key=key, reverse=descending)
    first = group.pop(0)
    if key is not None:
        keep_key = key(first)
        while len(group):
            if key(group[0]) != keep_key:
                break
            group.pop(0)
    return group


def get_files_with_no_date_in_path(group):
    rtn = []
    for fname in group:
        year, month, day, _ = get_date_from_path(fname)
        if year == 0:
            rtn.append(fname)

    if len(rtn) == 0:  # All had years; see if any don't have months
        for fname in group:
            year, month, day, _ = get_date_from_path(fname)
            if month == 0:
                rtn.append(fname)

    if len(rtn) == 0:  # All had years and months; see if any don't have days
        for fname in group:
            year, month, day, _ = get_date_from_path(fname)
            if day == 0:
                rtn.append(fname)

    if len(rtn) == len(group):
        return []  # None had paths so we don't know what to keep; just keep all
    return rtn


def clean_main():
    to_check = {}
    have = {}

    # Find all the files to check
    for filename in glob.iglob(path_join(source, '/**/*'), recursive=not norecurse):
        if filename.find('@eaDir') >= 0:  # Synology use only; need a way to configure these
            continue
        if not os.path.isfile(filename):
            if os.path.isdir(filename):
                print(f'Adding files from source folder {filename}')
            continue
        sz = os.path.getsize(filename)
        path = filename
        #path = os.path.abspath(filename)  # probably redundant
        if sz not in to_check:
            to_check[sz] = [path]
        else:
            to_check[sz].append(path)

    if target:
        # Find all the files that may have existing dups, making sure to 
        # exclude the files found above so we don't treat any files as dups
        # of themselves.
        spath = source
        if spath[-1] != '/':
            spath += '/'
        for filename in glob.iglob(path_join(target, '/**/*'), recursive=True):
            if filename.find('@eaDir') >= 0:  # Synology use only; need a way to configure these
                continue
            if filename[:len(spath)] == spath: # Skip files in source folder
                continue
            if not os.path.isfile(filename):
                if os.path.isdir(filename):
                    print(f'Adding files from target folder {filename}')
                continue
            sz = os.path.getsize(filename)
            path = filename
            #path = os.path.abspath(filename)  # probably redundant
            if sz not in to_check:
                continue
            if sz not in have:
                have[sz] = {path: None}
            else:
                have[sz][path] = None

        # Now check each file. If there are no others with same size, we are done. 
        # Otherwise we need to compute hashes of contents and look for a match.
        for sz in to_check:
            if sz not in have:
                continue
            # Compute hashes of targets
            to_hash = have[sz]
            for fname in to_hash.keys():
                to_hash[fname] = hash_file(fname)

            for fname in to_check[sz]:
                h = hash_file(fname)
                for fname2 in to_hash.keys():
                    if h == to_hash[fname2]:
                        # Hashes match, do deep compare if not disabled
                        if nodeep or files_match(fname, fname2):
                            print(f"Deleting {fname} which is a duplicate of {fname2}")
                            remove_file(fname)
                            break
    else:
        # Target was not set, we are looking within a directory
        for sz in to_check:
            if len(to_check[sz]) < 2:
                continue
            hashes = {}
            for fname in to_check[sz]:
                h = hash_file(fname)
                if h not in hashes:
                    hashes[h] = [fname]
                else:
                    hashes[h].append(fname)

            for h in hashes.keys():
                if len(hashes[h]) < 2:
                    continue
                # We have 2 or more files with the same hash.
                files = list(hashes[h])
                # We pop first file from the list, do pairwise compares with the rest, and 
                # remove any others that match and put them in a set; after dealing with that
                # set we repeat the process with any remaining ones in the list, if any.
                while len(files) > 1:
                    fname = files.pop(0)
                    i = 0
                    group = [fname]
                    while i < len(files):
                        if nodeep or files_match(fname, files[i]):
                            group.append(files.pop(i))
                        else:
                            i += 1
                    print(f'Duplicate group {group}')
                    # TODO: figure out which to delete
                    if newest:
                        to_delete = process_dup_group(group, key=os.path.getmtime, descending=True)
                    elif oldest:
                        to_delete = process_dup_group(group, key=os.path.getmtime, descending=False)
                    elif shortest:
                        to_delete = process_dup_group(group, key=lambda n: len(n.split('/')), descending=False)
                    elif longest:
                        to_delete = process_dup_group(group, key=lambda n: len(n.split('/')), descending=True)
                    else:
                        to_delete = get_files_with_no_date_in_path(group)

                    if len(to_delete):
                        print(f'Deleting subgroup {to_delete}')
                        for fname in to_delete:
                            remove_file(fname)

                    if len(group) - len(to_delete) > 1 and force:
                        # Do a second pass, just using lexical ordering
                        to_delete = process_dup_group([x for x in group if x not in to_delete])
                        print(f'Force deleting subgroup {to_delete}')
                        for fname in to_delete:
                            remove_file(fname)



def move_main():
    for filename in glob.iglob(path_join(source, '/**/*'), recursive=not norecurse):
        if not os.path.isfile(filename):
            continue
        if filename.find('@eaDir') >= 0:  # Synology use only; need a way to configure these
            continue
        if filename in done:
            continue
        move_process(filename)

