#!/bin/sh
# args: pkg_name parent
# eg ./make_pkg-upload.jamf.sh Zotero com.github.ruphysics.pkg.Zotero
override="/Users/padmin/Library/AutoPkg/RecipeOverrides/"
list="/Users/padmin/Library/Application Support/AutoPkgr/recipe_list.txt"



pkg_name=$1
pkg_parent=$2
pkg_category=$3

mkdir "$pkg_name"
cd "$pkg_name" || exit 1

cp ../Template-pkg-upload.jamf.recipe "$pkg_name"-pkg-upload.jamf.recipe
sed -e "s/XX/$pkg_name/g;s/com.github.ruphysics.pkg.YY/$pkg_parent/g;s/Apps/$pkg_category/g" -i ".bak"  "$pkg_name"-pkg-upload.jamf.recipe
# bbedit -w --resume "$pkg_name"-pkg-upload.jamf.recipe

echo make override "com.github.tmuphysics.jamf.${pkg_name}-pkg-upload"
autopkg make-override "com.github.tmuphysics.jamf.${pkg_name}-pkg-upload"
bbedit -w --resume "${override}/$pkg_name"-pkg-upload.jamf.recipe

echo run "local.jamf.${pkg_name}-pkg-upload"
autopkg  run  -vv "local.jamf.${pkg_name}-pkg-upload"
echo  before:
grep -i  $pkg_name "$list"
sed -e "s/local.jss.${pkg_name}/local.jamf.${pkg_name}-pkg-upload/g;" -i ".bak" "$list"
echo  after:
grep -i  $pkg_name "$list"
echo  done!

