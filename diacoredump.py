"""
  pydia: diacoredump.py - 2021.12
  ================================================
  
 Dump dia registry as json files to reproduce register_type and register_shapes
 
  Usage:This script has to be run from dia, so put it in your user dia directory.
  The trigger the script from the menu Debug where an entry "Dia core dumper"
  should be available

  Note: Experimental, will be obsolete if we found a way to use libdia /pydia libraries
  Author: SoSie@sos-productions.com
  License: LGPL
"""


import dia

import json

import jsonpickle
from json import JSONEncoder

import os
import locale  
import re
os.environ["PYTHONIOENCODING"] = "utf-8"
myLocale=locale.setlocale(category=locale.LC_ALL, locale="fr_FR.UTF-8");
import sys
python2 = (sys.version_info[0] == 2)


#See duai python2-3 installation on https://sosie-js.github.io/python-dia/
if python2:
    PREFIX="/usr" 
else:
    PREFIX="/opt" 

DIA_BASE_PATH=os.path.join(PREFIX,"share","dia")



# The user home dia python will store resulting core files
# and extract dia version and to use it as core sub directory

if 'HOME' not in os.environ:
    os.environ['HOME'] = os.pathsep + 'tmp'
target_base=os.path.join(os.environ['HOME'], '.dia', 'python')
 

try:
    #create if none
    target_dir=os.path.join(target_base,'core')
    os.mkdir(target_dir)
except OSError as error:
    #print(error)   
    pass

DIA_CMD=str(os.path.join(PREFIX,'bin','dia'))

import subprocess
if python2:
    try:
        byteOutput = subprocess.check_output([DIA_CMD, '-v'],stderr= subprocess.STDOUT)
        output=byteOutput.decode('UTF-8').rstrip()
    except subprocess.CalledProcessError as e:
        print("Error in '+DIA_CMD+' -v:\n", e.output)
else:
    output = subprocess.getoutput(DIA_CMD+' -v')

core_dir=output[:output.find(',')].replace('Dia version DIA_','Dia version ').replace('Dia version ','')

try:
    #create if none
    target_dir=os.path.join(target_base,'core',core_dir)
    os.mkdir(target_dir)
except OSError as error:
    #print(error)   
    pass



"""
  class AttrDict(dict):
            def __init__(self, *args, **kwargs):
                super(AttrDict, self).__init__(*args, **kwargs)
                self.__dict__ = self
                
        data = AttrDict()
        doNothing = lambda *args: None
        data.update({'active_layer':Layer(), 'update_extents':  doNothing})
"""


def json_dump(dump):
    """ 
        json_dump for any object, solve serializablelisable issue 
        Adapted from https://pynative.com/make-python-class-json-serializable/
    """
    #Encode Object into JSON formatted Data using jsonpickle")
    dumpJSON = jsonpickle.encode(dump, unpicklable=False)
    return dumpJSON
    
def beautiFyJSON(dumpJSON):
    obj=json.loads(dumpJSON)
    #Writing JSON Encode data into Python String")
    dumpJSONData = json.dumps(obj, indent=4)
    return dumpJSONData

#Some tuple props has inconsistent values when stringified
# ie instead of having point like for real type, have comma. 
# Conversion of such types internally to real has loopholes
# we force them to real with  ie for point :  (X,xxx,Y,yyy) becomes (X.xxx,Y.yyy)

def _coord(x):
    cx=str(x)
    return float(cx.replace(",",".")) #x coordinate 
  
def _color_component(x):
    cx=str(x) 
    return float(cx.replace(",",".")) # () double: color component [0 .. 1.0] 
     
def _point(x,y):
    x=_coord(x) #x coordinate 
    y=_coord(y) #y coordinate 
    return {"x":x, "y":y}
    
def _tuple(object):
    if isinstance(object, dict) :
        for key, value in object.items():
            object[key]=_tuple(value)
        object=object.values()
    elif isinstance(object, list) :
            object=(tuple(list(object)))
    if  "dict_values(" in str(object) : #it could have been list but not...
        object=tuple(list(object))
    return object


def normalizePropertyValue(pvalue,ptype):
    
    if(ptype == "point"):
        [cx, cy]=[t(s) for t,s in zip((str,str),re.search('^\(([-+]?\d*\,\d+|\d+),([-+]?\d*\,\d+|\d+)\)$',str(pvalue)).groups())]
        point=_point(cx,cy)
        pvalue=_tuple(point) #(_tuple(list(point.values())))
    elif(ptype == "rect"):
        [cx,cy,dx,dy]=[t(s) for t,s in zip((str,str,str,str),re.search('^\(\(([-+]?\d*\,\d+|\d+),([-+]?\d*\,\d+|\d+)\),\(([-+]?\d*\,\d+|\d+),([-+]?\d*\,\d+|\d+)\)\)$',str(pvalue)).groups())]
        point1=_point(cx,cy)
        point2=_point(dx,dy)
        rect={"point1":point1,"point2":point2}
        pvalue=_tuple(rect) #(_tuple(rect.values()))
    elif(ptype == "colour"):
        [cx,cy,dx,dy]=[t(s) for t,s in zip((str,str,str,str),re.search('^\(([-+]?\d*\,\d+|\d+),([-+]?\d*\,\d+|\d+),([-+]?\d*\,\d+|\d+),([-+]?\d*\,\d+|\d+)\)$',str(pvalue)).groups())]
        red = _color_component(cx)  # () double: red color component [0 .. 1.0]  
        green = _color_component(cy)  # () double: green color component [0 .. 1.0] 
        blue = _color_component(dx)  # () double: blue color component [0 .. 1.0] 
        alpha = _color_component(dy)  # () double: alpha color component [0 .. 1.0] 
        color={"red": red, "green":green, "blue":blue, "alpha":alpha}
        colour=_tuple(color) #(_tuple(color.values()))
        pvalue=colour
    elif(ptype == "color"):
        red=pvalue.red
        green=pvalue.green
        blue=pvalue.blue
        alpha=pvalue.alpha
        color={"red": red, "green":green, "blue":blue, "alpha":alpha}
        pvalue=_tuple(color)#_tuple(color.values())
    elif(ptype == "font"):
        font={"name":pvalue.name,"family":pvalue.family, "style":pvalue.style}
        pvalue=_tuple(font) #_tuple(font.values())
    elif(ptype == "text"):
        #raise(Exception(prop.name+" is a text(#"+str(prop.value.color.blue)+"#"+str(prop.value.color.green)+"#"+str(prop.value.color.red)+"#"+str(prop.value.color.alpha)+","+str(prop.value.height)+",["+str(prop.value.font.family)+":"+str(prop.value.font.name)+":"+str(prop.value.font.style)+"],"+str(prop.value.position)+"="+str(prop.value.text)+")"))
        text={
            "color": normalizePropertyValue(pvalue.color, "color"),#{ "red":str(prop.value.color.red), "green":str(prop.value.color.green),"blue": str(prop.value.color.blue),"alpha":str(prop.value.color.alpha)},
            "font": normalizePropertyValue(pvalue.font, "font"), #{"name":str(prop.value.font.name),"family":str(prop.value.font.family), "style":str(prop.value.font.style)},
            "height": pvalue.height,
            "position": normalizePropertyValue(pvalue.position,"point"),
            "text": pvalue.text
        }
        #others property types, the whole list has been determined using a patched allprops.py
        """
        [
            "arrow",
            "bezpointarray",
            "bool",
            "connpoint_line",
            "darray",
            "dict",
            "endpoints",
            "enum",
            "enumarray",
            "file",
            "fontsize",
            "int",
            "length",
            "linestyle",
            "multistring",
            "pattern",
            "pixbuf",
            "pointarray",
            "real",
            "static",
            "string",
        ]
        """
        pvalue=_tuple(text) #_tuple(text.values())
    return pvalue

def normalizeObjectTypeName(s):
    kt = s.split(" - ")
    if len(kt) == 2 :
        if len(kt[0]) == 0 :
            sp = "<unnamed>"
        else :
            sp = kt[0]
        st = kt[1]
    else :
        sp = "<broken>"
        st = kt[0]
    return (sp,st)
    
def get_object_default_properties(name):
    
    otypes=dia.registered_types() #
    properties={}
    error=""
    [sp, st] = normalizeObjectTypeName(name)
    
    stp= sp + " - " + st
    
    try:
    
        if python2 :
        
            if otypes.has_key(st) :
                otype= dia.get_object_type(st)
                o_real, h5, h6 = otype.create(0,0)
            elif  otypes.has_key(stp) :
                otype= dia.get_object_type(stp)
                o_real, h5, h6 = otype.create(0,0)
            else :
                otype = None
                o_real = None
                print("Failed to create object", sp, st)
        
        else:
            
            if st in otypes :
                otype= dia.get_object_type(st)
                o_real, h5, h6 = otype.create(0,0)
            elif  stp in otypes :
                otype= dia.get_object_type(stp)
                o_real, h5, h6 = otype.create(0,0)
            else :
                otype = None
                o_real = None
                error="Failed to create object "+ stp
    except BaseException as e:
        otype = None
        o_real = None
        brokens=["<broken> - Group", "BPMN - Group"] #RuntimeError('Type has no ops!?')
        if not stp in brokens  :
            error="Failed to create object" + stp  +"\n"+str(e)
            
    if not o_real is None :
        #print(str(type(otype))+" of "+otname)
        #print(str(type(o_real)))
        
        for key in o_real.properties.keys():
            property={}
            prop=o_real.properties[key] 
            property["name"]=prop.name
            ptype=prop.type
            property["type"]=ptype
            pvalue=normalizePropertyValue(prop.value, ptype)
            property["value"]=pvalue
            property["visible"]=prop.visible
            properties[prop.name]=property
        
        # XXX: there really should be a way to safely delete an object. This one will crash:
        # - when the object got added somewhere 
        # - any object method gets called afterwards
        o_real.destroy()
        del o_real
    return (properties, otype, error)
    

    
def dia_core_dumper(data, flags):
    """ Dump the core of dia, ie all dia objects as json definition files holding default properties values"""
    otypes=dia.registered_types() #type: <class 'dict'>, len: 1339 keys() : [ names ], values() [ <DiaObjectType>]
    fails=0
    errors=[]
    ntypes={}
    for key, value in otypes.items() :      
        if( key !=value.name):
           # print("["+key+"="+value.name+"]")
            fails=fails+1
    
        [properties, otype, error]=get_object_default_properties(key)
           
        if(not otype is None):
            
            oprops={
                'name' : otype.name,
                'version': otype.version,
            }
            
            oprops_full={}
            oprops_full['name'] = oprops['name']
            oprops_full['version'] = oprops['version']
            oprops_full['properties'] = properties
            
            #ntypes[key]=
            ntypes[otype.name]=oprops_full

        else:
            print(error)
            errors.append(error)
    #print("["+key+"="+str(type(ntypes[key]))+"]",ntypes[key].name)
    print("Objected Types exportation : "+str(len(ntypes))+" succeeded, "+str(len(errors))+" failed and "+str(fails)+ " coherency failures found")
    
    ojsontypes=json_dump(ntypes)
    objsontypes = beautiFyJSON(ojsontypes)
    with open(str(os.path.join(target_dir,"registered_types_full.json")), 'w') as outfile:
        outfile.write(objsontypes )
    
    
    
    osheets=dia.registered_sheets() #[ <class 'dia.Sheet'>, .. 
    """
    >>> print(osheets[0])
AADL Shapes
>>> print(type(osheets[0]))
<class 'dia.Sheet'>
>>> print(type(osheets[0].description))
<class 'str'>
>>> print(osheets[0].description)
AADL Shapes
>>> print(osheets[0].filename)
/usr/share/dia/sheets/AADL.sheet
>>> print(osheets[0].name)
AADL
>>> print(osheets[0].user)
0

#objects [( objecttype1,objectype_description_translated, ?) 
>>> print(osheets[0].objects[0][0].name)
AADL - Process
>>> print(osheets[0].objects[0][1])
Traiter
>>> print(osheets[0].objects[0][2])
None

    """
    
    
   
    
    otypes={}
    sheets=[]
    errors=[]
    warnings=0
    with open(str(os.path.join(target_dir,"warnings.txt")), 'w') as wrnfile:
        
        float_tuples=['point','rect','colour']
         
        for osheet in osheets:
            
            """
            objects=[]
            for object in osheet.objects:
                objects.append({
                    "bounding_box":object.bounding_box , #Box covering all the object.
                    "connections": object.connections, #Vector of connection points.
                    "handles":object.handles ,#'Vector of handles.
                    "parent" : object.parent, #The parent object when parenting is in place, None otherwise.'
                    "properties": object.properties,#Dictionary of object properties.
                })
            """  
            objects=[]

            #print(str(osheet.objects))
           
    
            for object in osheet.objects:
                    """
                    {
                        name: object[0].name,
                        version: object[0].version
                    }
                    """
                   
                    
                    #leech the props of the real object matching the type
                    otype=object[0]
                    otname=otype.name
                    
                    [properties, otype, error]=get_object_default_properties(otname)
           
                    if(not otype is None):
                    
                        oprops={
                            'name' : otype.name,
                            'version': otype.version,
                        }
                        
                        oprops_full={}
                        oprops_full['name'] = oprops['name']
                        oprops_full['version'] = oprops['version']
                        oprops_full['properties'] = properties
                        
                        otypes[otype.name]=oprops_full
                        
                        if(otype.name in ntypes.keys()):
                            del  ntypes[otype.name]
                            
                        s_name=osheet.name
                        s_name=str(s_name.encode('ascii', errors = 'ignore').decode('ascii'))
                        
                        
                        if(not " - " in otype.name):     
                            s_type = otype.name 
                            s_type=s_name+" - "+  otype.name.replace(s_name+"_","")
                            warning="WARNING:In sheet '"+s_name +"' ("+osheet.description+"),\n\t orphean object type '"+ otype.name+"' \n\t object name SHOULD BE (GUESSING) : '"+s_type+"' in "+osheet.filename
                            wrnfile.write("\n"+warning)
                            warnings=warnings+1
                            
                        #if(s_name+" - "+otname != otype.name):
                        #    ot_name=str(otname.encode('ascii', errors = 'ignore').decode('ascii'))
                        #   warning="WARNING:In sheet '"+s_name +"' , otname ("+ot_name+") missmatches otype.name("+otype.name+")"
                        #   wrnfile.write("\n"+warning)
                        #    warnings=warnings+1
                            
                        otpict=object[2]
                        objects.append([oprops,otname,otpict])
                    
                    else:
                        print(error)
                        errors.append(error)
                    
            sheets.append({
                "description": osheet.description, #The description for the sheet.
                "filename" : osheet.filename ,#The filename for the sheet.
                "name": osheet.name , #The name for the sheet.
                "objects": objects  , #The list of sheet objects referenced by the sheet. 
                "user": osheet.user , #The sheet scope is user provided, not system.
            })
        
     
    
        ojsontypes=json_dump(otypes)
        objsontypes = beautiFyJSON(ojsontypes)
        with open(str(os.path.join(target_dir,"registered_types.json")), 'w') as outfile:
            outfile.write(objsontypes )
    
    
    
        ojsontypes=json_dump(ntypes)
        objsontypes = beautiFyJSON(ojsontypes)
        with open(str(os.path.join(target_dir,"broken_types.json")), 'w') as outfile:
            outfile.write(objsontypes )
        
        """
        sheets.append({
            "description": "Broken",
            "filename" : osheet.filename ,#The filename for the sheet.
            "name": "Broken objects" , #The name for the sheet.
            "objects": ntypes, #The list of sheet objects referenced by the sheet. 
            "user": "", #The sheet scope is user provided, not system.
        })
        """
        nsheets={}
        for ntype , ontype in ntypes.items():
            [sp,st]=normalizeObjectTypeName(ntype)
            if not sp in nsheets :
                nsheets[sp]= {
                    "description": sp+" Shapes",
                    "filename": os.path.join(DIA_BASE_PATH,"sheets",sp+".sheet"),
                    "name": sp,
                    "objects": []
                    }
            nsheets[sp]["objects"].append([ {
                    "name": ontype["name"], #or ntype
                    "version": ontype["version"]
                },
                ntype,
                None])
                
        jsonsheets=json_dump(nsheets)
        objsonsheets = beautiFyJSON(jsonsheets)
        with open(str(os.path.join(target_dir,"unregistered_sheets.json")), 'w') as outfile:
            outfile.write(objsonsheets )
        
        jsonsheets=json_dump(sheets)
        objsonsheets = beautiFyJSON(jsonsheets)
        with open(str(os.path.join(target_dir,"sheets.json")), 'w') as outfile:
            outfile.write(objsonsheets )

      
        #Note: messages with level < 2 seemed filtered, I don't know how to popup them
        dia.message(2, " Dia core registry dumped : "+str(len(otypes)) +" dia objects found!\nExportation of their json definition in \n"+str(target_dir)+"/ ! \nIt's done with "+str(warnings)+ " warning(s) and "+str(len(errors))+" errors(s)") # Here are the big list of "+str(len(json.loads(ojsontypes)))+" "+str(type(json.loads(ojsontypes)))+"\n"+objsontypes)
       
## Adds the entry "Dia Core dumper" in the menu "Debug" so dia_core_dumper script can be triggered from there
dia.register_callback("Dia core dumper", "<Display>/Debug/DiaCoreDumper", dia_core_dumper)

